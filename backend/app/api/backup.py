"""
数据备份与恢复 API
"""
import json
import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, SignLog, Setting, NotifyChannel, AccountNotify, ApiToken, User, AuditAction
from app.schemas import ApiResponse
from app.services.audit import log_action
from app.api.deps import get_current_user

router = APIRouter(prefix="/backup", tags=["备份恢复"])


@router.get("/export", response_class=StreamingResponse)
def export_backup(
    request: Request,
    include_logs: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出数据备份

    Args:
        include_logs: 是否包含签到日志（可选，默认不包含）
    """
    backup_data = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "accounts": [],
        "settings": [],
        "notify_channels": [],
        "account_notifies": [],
    }

    # 导出账号（不包含敏感的 session_cookie）
    accounts = db.query(Account).all()
    for acc in accounts:
        backup_data["accounts"].append({
            "id": acc.id,
            "session_cookie": acc.session_cookie,  # 加密存储时需要处理
            "anyrouter_user_id": acc.anyrouter_user_id,
            "username": acc.username,
            "display_name": acc.display_name,
            "is_active": acc.is_active,
            "health_status": acc.health_status,
            "created_at": acc.created_at.isoformat() if acc.created_at else None,
        })

    # 导出设置
    settings = db.query(Setting).all()
    for s in settings:
        backup_data["settings"].append({
            "key": s.key,
            "value": s.value,
        })

    # 导出推送渠道
    channels = db.query(NotifyChannel).all()
    for ch in channels:
        backup_data["notify_channels"].append({
            "id": ch.id,
            "type": ch.type,
            "name": ch.name,
            "config": ch.config,
            "is_enabled": ch.is_enabled,
        })

    # 导出账号-推送关联
    notifies = db.query(AccountNotify).all()
    for n in notifies:
        backup_data["account_notifies"].append({
            "account_id": n.account_id,
            "channel_id": n.channel_id,
            "is_enabled": n.is_enabled,
            "notify_config": n.notify_config,
        })

    # 可选：导出签到日志
    if include_logs:
        backup_data["sign_logs"] = []
        logs = db.query(SignLog).order_by(SignLog.sign_time.desc()).limit(1000).all()
        for log in logs:
            backup_data["sign_logs"].append({
                "account_id": log.account_id,
                "sign_time": log.sign_time.isoformat() if log.sign_time else None,
                "success": log.success,
                "message": log.message,
                "reward_quota": log.reward_quota,
            })

    # 记录审计日志
    log_action(
        db=db,
        action=AuditAction.BACKUP_EXPORT,
        user_id=current_user.id,
        username=current_user.username,
        target_type="backup",
        detail={
            "include_logs": include_logs,
            "accounts": len(backup_data["accounts"]),
            "settings": len(backup_data["settings"]),
            "channels": len(backup_data["notify_channels"])
        },
        request=request
    )

    # 生成 JSON 文件
    json_str = json.dumps(backup_data, ensure_ascii=False, indent=2)
    buffer = io.BytesIO(json_str.encode('utf-8'))
    buffer.seek(0)

    filename = f"anyrouter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.post("/import", response_model=ApiResponse)
async def import_backup(
    request: Request,
    file: UploadFile = File(...),
    overwrite: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导入数据备份

    Args:
        file: 备份文件
        overwrite: 是否覆盖现有数据
    """
    try:
        content = await file.read()
        backup_data = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="无效的备份文件格式")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"读取文件失败: {str(e)}")

    # 验证备份版本
    if backup_data.get("version") != "1.0":
        raise HTTPException(status_code=400, detail="不支持的备份版本")

    imported_counts = {
        "accounts": 0,
        "settings": 0,
        "notify_channels": 0,
        "account_notifies": 0,
    }

    try:
        # 导入设置
        if "settings" in backup_data:
            for s in backup_data["settings"]:
                existing = db.query(Setting).filter(Setting.key == s["key"]).first()
                if existing:
                    if overwrite:
                        existing.value = s["value"]
                        imported_counts["settings"] += 1
                else:
                    db.add(Setting(key=s["key"], value=s["value"]))
                    imported_counts["settings"] += 1

        # 导入推送渠道
        channel_id_map = {}  # 旧 ID -> 新 ID 的映射
        if "notify_channels" in backup_data:
            for ch in backup_data["notify_channels"]:
                old_id = ch["id"]
                # 检查是否存在同名渠道
                existing = db.query(NotifyChannel).filter(NotifyChannel.name == ch["name"]).first()
                if existing:
                    if overwrite:
                        existing.type = ch["type"]
                        existing.config = ch["config"]
                        existing.is_enabled = ch["is_enabled"]
                        channel_id_map[old_id] = existing.id
                        imported_counts["notify_channels"] += 1
                    else:
                        channel_id_map[old_id] = existing.id
                else:
                    new_channel = NotifyChannel(
                        type=ch["type"],
                        name=ch["name"],
                        config=ch["config"],
                        is_enabled=ch["is_enabled"],
                    )
                    db.add(new_channel)
                    db.flush()  # 获取新 ID
                    channel_id_map[old_id] = new_channel.id
                    imported_counts["notify_channels"] += 1

        # 导入账号
        account_id_map = {}  # 旧 ID -> 新 ID 的映射
        if "accounts" in backup_data:
            for acc in backup_data["accounts"]:
                old_id = acc["id"]
                # 检查是否存在相同 anyrouter_user_id 的账号
                existing = None
                if acc.get("anyrouter_user_id"):
                    existing = db.query(Account).filter(
                        Account.anyrouter_user_id == acc["anyrouter_user_id"]
                    ).first()

                if existing:
                    if overwrite:
                        existing.session_cookie = acc["session_cookie"]
                        existing.username = acc.get("username")
                        existing.display_name = acc.get("display_name")
                        existing.is_active = acc.get("is_active", True)
                        account_id_map[old_id] = existing.id
                        imported_counts["accounts"] += 1
                    else:
                        account_id_map[old_id] = existing.id
                else:
                    new_account = Account(
                        session_cookie=acc["session_cookie"],
                        anyrouter_user_id=acc.get("anyrouter_user_id"),
                        username=acc.get("username"),
                        display_name=acc.get("display_name"),
                        is_active=acc.get("is_active", True),
                        health_status=acc.get("health_status", "unknown"),
                    )
                    db.add(new_account)
                    db.flush()
                    account_id_map[old_id] = new_account.id
                    imported_counts["accounts"] += 1

        # 导入账号-推送关联
        if "account_notifies" in backup_data:
            for n in backup_data["account_notifies"]:
                # 映射新 ID
                new_account_id = account_id_map.get(n["account_id"])
                new_channel_id = channel_id_map.get(n["channel_id"])

                if not new_account_id or not new_channel_id:
                    continue

                existing = db.query(AccountNotify).filter(
                    AccountNotify.account_id == new_account_id,
                    AccountNotify.channel_id == new_channel_id
                ).first()

                if existing:
                    if overwrite:
                        existing.is_enabled = n["is_enabled"]
                        existing.notify_config = n.get("notify_config")
                        imported_counts["account_notifies"] += 1
                else:
                    db.add(AccountNotify(
                        account_id=new_account_id,
                        channel_id=new_channel_id,
                        is_enabled=n["is_enabled"],
                        notify_config=n.get("notify_config"),
                    ))
                    imported_counts["account_notifies"] += 1

        db.commit()

        # 记录审计日志
        log_action(
            db=db,
            action=AuditAction.BACKUP_IMPORT,
            user_id=current_user.id,
            username=current_user.username,
            target_type="backup",
            detail={
                "overwrite": overwrite,
                "imported": imported_counts
            },
            request=request
        )

        return ApiResponse(
            success=True,
            message="数据导入成功",
            data=imported_counts
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/info", response_model=ApiResponse)
def get_backup_info(db: Session = Depends(get_db)):
    """获取当前数据统计信息"""
    return ApiResponse(
        success=True,
        data={
            "account_count": db.query(Account).count(),
            "sign_log_count": db.query(SignLog).count(),
            "notify_channel_count": db.query(NotifyChannel).count(),
            "setting_count": db.query(Setting).count(),
        }
    )
