"""
系统设置 API
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting, User, AuditAction, NotifyChannel
from app.schemas import ApiResponse, SettingsResponse, SettingsUpdate
from app.services.scheduler import update_sign_schedule, update_health_check_schedule, update_log_cleanup_schedule
from app.services.audit import log_action
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["系统设置"])


DEFAULT_SETTINGS = {
    "auto_sign_enabled": False,
    "auto_sign_time": "08:00",
    "health_check_enabled": True,
    "health_check_interval": 6,
    "sign_retry_enabled": True,
    "sign_max_retries": 3,
    "sign_retry_interval": 30,
    "sign_notify_enabled": False,
    "sign_notify_channel_ids": [],
    "quota_warning_threshold": 5.0,
    "audit_log_retention_days": 0,
    "system_log_retention_days": 0,
}


def get_setting(db: Session, key: str, default=None):
    """获取单个设置"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        try:
            return json.loads(setting.value)
        except:
            return setting.value
    return default


def set_setting(db: Session, key: str, value):
    """设置单个配置"""
    setting = db.query(Setting).filter(Setting.key == key).first()

    if setting:
        setting.value = json.dumps(value) if not isinstance(value, str) else value
        setting.updated_at = datetime.now()
    else:
        setting = Setting(
            key=key,
            value=json.dumps(value) if not isinstance(value, str) else value
        )
        db.add(setting)


def normalize_channel_ids(channel_ids) -> list[int]:
    """清理推送渠道 ID 列表，保留原顺序并去重。"""
    normalized = []
    seen = set()
    if not isinstance(channel_ids, list):
        return normalized
    for channel_id in channel_ids:
        try:
            normalized_id = int(channel_id)
        except (TypeError, ValueError):
            continue
        if normalized_id <= 0 or normalized_id in seen:
            continue
        seen.add(normalized_id)
        normalized.append(normalized_id)
    return normalized


@router.get("", response_model=ApiResponse)
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    result = {}
    for key, default in DEFAULT_SETTINGS.items():
        result[key] = get_setting(db, key, default)
    result["sign_notify_channel_ids"] = normalize_channel_ids(
        result.get("sign_notify_channel_ids") or []
    )

    return ApiResponse(
        success=True,
        data=SettingsResponse(**result)
    )


@router.put("", response_model=ApiResponse)
def update_settings(
    data: SettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新系统设置"""
    update_data = data.model_dump(exclude_unset=True)
    current_settings = {
        key: get_setting(db, key, default)
        for key, default in DEFAULT_SETTINGS.items()
    }

    merged_settings = {**current_settings, **update_data}
    quota_warning_threshold = merged_settings.get("quota_warning_threshold", 5.0)
    sign_notify_enabled = bool(merged_settings.get("sign_notify_enabled", False))
    sign_notify_channel_ids = normalize_channel_ids(merged_settings.get("sign_notify_channel_ids") or [])
    if "sign_notify_channel_ids" in update_data:
        update_data["sign_notify_channel_ids"] = sign_notify_channel_ids

    if quota_warning_threshold is None or quota_warning_threshold < 0:
        raise HTTPException(status_code=400, detail="额度告警阈值不能小于 0")

    for retention_key, retention_label in (
        ("audit_log_retention_days", "审计日志保留天数"),
        ("system_log_retention_days", "系统日志保留天数"),
    ):
        retention_days = merged_settings.get(retention_key, 0)
        if retention_days is None:
            continue
        if not isinstance(retention_days, int) or isinstance(retention_days, bool):
            raise HTTPException(status_code=400, detail=f"{retention_label}必须是整数")
        if retention_days < 0 or retention_days > 365:
            raise HTTPException(status_code=400, detail=f"{retention_label}需在 0-365 之间（0 表示不自动清理）")

    if sign_notify_enabled and not sign_notify_channel_ids:
        raise HTTPException(status_code=400, detail="启用签到推送时请选择推送渠道")
    if sign_notify_enabled:
        enabled_channel_count = db.query(NotifyChannel).filter(
            NotifyChannel.id.in_(sign_notify_channel_ids),
            NotifyChannel.is_enabled == True
        ).count()
        if enabled_channel_count != len(sign_notify_channel_ids):
            raise HTTPException(status_code=400, detail="签到推送只能选择已启用的推送渠道")

    for key, value in update_data.items():
        if value is not None:
            set_setting(db, key, value)

    db.commit()

    # 更新签到定时任务
    if "auto_sign_enabled" in update_data or "auto_sign_time" in update_data:
        update_sign_schedule()

    # 更新健康检查定时任务
    if "health_check_enabled" in update_data or "health_check_interval" in update_data:
        update_health_check_schedule()

    # 更新日志清理定时任务
    if "audit_log_retention_days" in update_data or "system_log_retention_days" in update_data:
        update_log_cleanup_schedule()

    # 记录审计日志
    audit_detail = update_data.copy()

    log_action(
        db=db,
        action=AuditAction.SETTING_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="setting",
        detail=audit_detail,
        request=request
    )

    return ApiResponse(success=True, message="设置保存成功")


@router.get("/scheduler", response_model=ApiResponse)
def get_scheduler_status(db: Session = Depends(get_db)):
    """获取调度器状态"""
    from app.services.scheduler import scheduler

    enabled = get_setting(db, "auto_sign_enabled", False)
    sign_time = get_setting(db, "auto_sign_time", "08:00")

    job = scheduler.get_job("auto_sign")
    next_run = None
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")

    return ApiResponse(success=True, data={
        "enabled": enabled,
        "sign_time": sign_time,
        "next_run": next_run,
        "running": scheduler.running
    })
