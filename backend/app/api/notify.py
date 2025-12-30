"""
推送渠道管理 API
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NotifyChannel, AccountNotify, User, AuditAction
from app.schemas import (
    NotifyChannelCreate, NotifyChannelUpdate, NotifyChannelResponse,
    AccountNotifyResponse, AccountNotifyUpdate,
    ApiResponse
)
from app.services import NotifyFactory
from app.services.audit import log_action
from app.api.deps import get_current_user

router = APIRouter(prefix="/notify", tags=["推送管理"])


@router.get("/channels", response_model=ApiResponse)
def get_channels(db: Session = Depends(get_db)):
    """获取所有推送渠道"""
    channels = db.query(NotifyChannel).order_by(NotifyChannel.created_at.desc()).all()

    result = []
    for channel in channels:
        config = json.loads(channel.config)
        # 隐藏敏感信息
        safe_config = {}
        for key, value in config.items():
            if 'secret' in key.lower() or 'password' in key.lower() or 'token' in key.lower():
                safe_config[key] = "******" if value else ""
            else:
                safe_config[key] = value

        result.append(NotifyChannelResponse(
            id=channel.id,
            type=channel.type,
            name=channel.name,
            config=safe_config,
            is_enabled=channel.is_enabled,
            created_at=channel.created_at,
            updated_at=channel.updated_at
        ))

    return ApiResponse(success=True, data=result)


@router.post("/channels", response_model=ApiResponse)
def create_channel(
    data: NotifyChannelCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """添加推送渠道"""
    # 验证渠道类型
    supported_types = NotifyFactory.get_supported_types()
    if data.type not in supported_types:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的渠道类型，支持: {', '.join(supported_types)}"
        )

    channel = NotifyChannel(
        type=data.type,
        name=data.name,
        config=json.dumps(data.config)
    )

    db.add(channel)
    db.commit()
    db.refresh(channel)

    # 记录审计日志
    log_action(
        db=db,
        action=AuditAction.CHANNEL_CREATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="channel",
        target_id=channel.id,
        target_name=channel.name,
        detail={"type": data.type},
        request=request
    )

    return ApiResponse(
        success=True,
        message="推送渠道添加成功",
        data={"id": channel.id}
    )


@router.put("/channels/{channel_id}", response_model=ApiResponse)
def update_channel(
    channel_id: int,
    data: NotifyChannelUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新推送渠道"""
    channel = db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    changes = {}

    if data.name is not None:
        if channel.name != data.name:
            changes["name"] = f"{channel.name} -> {data.name}"
        channel.name = data.name

    if data.config is not None:
        # 合并配置，保留未更新的敏感字段
        old_config = json.loads(channel.config)
        new_config = data.config

        for key, value in new_config.items():
            if value == "******":
                # 保留原值
                new_config[key] = old_config.get(key, "")

        channel.config = json.dumps(new_config)
        changes["config"] = "已更新"

    if data.is_enabled is not None:
        if channel.is_enabled != data.is_enabled:
            changes["is_enabled"] = f"{channel.is_enabled} -> {data.is_enabled}"
        channel.is_enabled = data.is_enabled

    channel.updated_at = datetime.now()
    db.commit()

    # 记录审计日志
    log_action(
        db=db,
        action=AuditAction.CHANNEL_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="channel",
        target_id=channel.id,
        target_name=channel.name,
        detail=changes if changes else None,
        request=request
    )

    return ApiResponse(success=True, message="渠道更新成功")


@router.delete("/channels/{channel_id}", response_model=ApiResponse)
def delete_channel(
    channel_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除推送渠道"""
    channel = db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    channel_name = channel.name
    channel_type = channel.type

    # 删除关联配置
    db.query(AccountNotify).filter(AccountNotify.channel_id == channel_id).delete()

    db.delete(channel)
    db.commit()

    # 记录审计日志
    log_action(
        db=db,
        action=AuditAction.CHANNEL_DELETE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="channel",
        target_id=channel_id,
        target_name=channel_name,
        detail={"type": channel_type},
        request=request
    )

    return ApiResponse(success=True, message="渠道删除成功")


@router.post("/channels/{channel_id}/test", response_model=ApiResponse)
def test_channel(channel_id: int, db: Session = Depends(get_db)):
    """测试推送渠道"""
    channel = db.query(NotifyChannel).filter(NotifyChannel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="渠道不存在")

    try:
        config = json.loads(channel.config)
        notifier = NotifyFactory.create(channel.type, config)
        success = notifier.test()

        if success:
            return ApiResponse(success=True, message="测试消息发送成功")
        else:
            return ApiResponse(success=False, message="测试消息发送失败")

    except Exception as e:
        return ApiResponse(success=False, message=f"测试失败: {str(e)}")


@router.get("/accounts/{account_id}", response_model=ApiResponse)
def get_account_notify(account_id: int, db: Session = Depends(get_db)):
    """获取账号的推送配置"""
    # 获取所有渠道
    channels = db.query(NotifyChannel).filter(NotifyChannel.is_enabled == True).all()

    # 获取账号已配置的渠道
    account_notifies = db.query(AccountNotify).filter(
        AccountNotify.account_id == account_id
    ).all()

    notify_map = {n.channel_id: n for n in account_notifies}

    result = []
    for channel in channels:
        account_notify = notify_map.get(channel.id)
        result.append(AccountNotifyResponse(
            channel_id=channel.id,
            channel_name=channel.name,
            channel_type=channel.type,
            is_enabled=account_notify.is_enabled if account_notify else False,
            notify_config=json.loads(account_notify.notify_config) if account_notify and account_notify.notify_config else {}
        ))

    return ApiResponse(success=True, data=result)


@router.put("/accounts/{account_id}", response_model=ApiResponse)
def update_account_notify(account_id: int, data: AccountNotifyUpdate, db: Session = Depends(get_db)):
    """更新账号的推送配置"""
    # 删除旧配置
    db.query(AccountNotify).filter(AccountNotify.account_id == account_id).delete()

    # 添加新配置
    for config in data.channels:
        account_notify = AccountNotify(
            account_id=account_id,
            channel_id=config.channel_id,
            is_enabled=config.is_enabled,
            notify_config=json.dumps(config.notify_config)
        )
        db.add(account_notify)

    db.commit()

    return ApiResponse(success=True, message="推送配置更新成功")
