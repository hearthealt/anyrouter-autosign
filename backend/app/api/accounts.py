"""
账号管理 API
"""
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, SignLog, NotifyChannel, AccountNotify, ApiToken
from app.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountInfo,
    LastSign, ApiResponse
)
from app.schemas.account import NotifyChannelBrief
from app.services import anyrouter_service
from app.utils import format_quota

router = APIRouter(prefix="/accounts", tags=["账号管理"])


def get_last_sign(db: Session, account_id: int) -> LastSign:
    """获取最后签到信息"""
    log = db.query(SignLog).filter(
        SignLog.account_id == account_id
    ).order_by(SignLog.sign_time.desc()).first()

    if log:
        return LastSign(
            time=log.sign_time,
            success=log.success,
            message=log.message
        )
    return None


def get_account_notify_channels(db: Session, account_id: int) -> List[NotifyChannelBrief]:
    """获取账号关联的推送渠道"""
    results = db.query(NotifyChannel).join(
        AccountNotify, AccountNotify.channel_id == NotifyChannel.id
    ).filter(
        AccountNotify.account_id == account_id,
        AccountNotify.is_enabled == True
    ).all()

    return [NotifyChannelBrief(id=c.id, type=c.type, name=c.name) for c in results]


@router.get("", response_model=ApiResponse)
def get_accounts(db: Session = Depends(get_db)):
    """获取账号列表"""
    accounts = db.query(Account).order_by(Account.created_at.desc()).all()

    result = []
    for account in accounts:
        result.append(AccountResponse(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            anyrouter_user_id=account.anyrouter_user_id,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
            notify_channels=get_account_notify_channels(db, account.id),
            last_sign=get_last_sign(db, account.id)
        ))

    return ApiResponse(success=True, data=result)


@router.post("", response_model=ApiResponse)
def create_account(data: AccountCreate, db: Session = Depends(get_db)):
    """添加账号"""
    # 验证 session_cookie 和 user_id
    success, user_info = anyrouter_service.get_user_info(data.session_cookie, data.user_id)

    if not success:
        raise HTTPException(status_code=400, detail=user_info.get("message", "验证失败"))

    # 检查是否已存在
    existing = db.query(Account).filter(
        Account.anyrouter_user_id == int(data.user_id)
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="该账号已存在")

    # 创建账号
    account = Account(
        session_cookie=data.session_cookie,
        anyrouter_user_id=int(data.user_id),
        username=user_info.get("username"),
        display_name=user_info.get("display_name")
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    # 同步 API Tokens
    sync_account_tokens(db, account)

    return ApiResponse(
        success=True,
        message="账号添加成功",
        data=AccountResponse(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            anyrouter_user_id=account.anyrouter_user_id,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
            notify_channels=[],
            last_sign=None
        )
    )


@router.get("/{account_id}", response_model=ApiResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取账号详情"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    return ApiResponse(
        success=True,
        data=AccountResponse(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            anyrouter_user_id=account.anyrouter_user_id,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
            notify_channels=get_account_notify_channels(db, account.id),
            last_sign=get_last_sign(db, account.id)
        )
    )


@router.put("/{account_id}", response_model=ApiResponse)
def update_account(account_id: int, data: AccountUpdate, db: Session = Depends(get_db)):
    """更新账号"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if data.session_cookie is not None or data.user_id is not None:
        # 使用新的 user_id 或现有的
        user_id = data.user_id or str(account.anyrouter_user_id)
        session_cookie = data.session_cookie or account.session_cookie

        # 验证新的凭证
        success, user_info = anyrouter_service.get_user_info(session_cookie, user_id)
        if not success:
            raise HTTPException(status_code=400, detail="凭证验证失败")

        account.session_cookie = session_cookie
        account.anyrouter_user_id = int(user_id)
        account.username = user_info.get("username")
        account.display_name = user_info.get("display_name")

    if data.is_active is not None:
        account.is_active = data.is_active

    account.updated_at = datetime.now()
    db.commit()

    return ApiResponse(success=True, message="账号更新成功")


@router.delete("/{account_id}", response_model=ApiResponse)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """删除账号"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 删除关联的推送配置
    db.query(AccountNotify).filter(AccountNotify.account_id == account_id).delete()

    # 删除签到日志
    db.query(SignLog).filter(SignLog.account_id == account_id).delete()

    # 删除账号
    db.delete(account)
    db.commit()

    return ApiResponse(success=True, message="账号删除成功")


@router.get("/{account_id}/info", response_model=ApiResponse)
def get_account_info(account_id: int, db: Session = Depends(get_db)):
    """获取账号实时信息"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, user_info = anyrouter_service.get_user_info(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    if not success:
        raise HTTPException(status_code=400, detail=user_info.get("message", "获取信息失败"))

    quota = user_info.get("quota", 0)
    used_quota = user_info.get("used_quota", 0)
    aff_history_quota = user_info.get("aff_history_quota", 0)

    return ApiResponse(
        success=True,
        data=AccountInfo(
            id=user_info.get("id"),
            username=user_info.get("username"),
            display_name=user_info.get("display_name"),
            role=user_info.get("role", 0),
            status=user_info.get("status", 0),
            quota=quota,
            used_quota=used_quota,
            request_count=user_info.get("request_count", 0),
            group=user_info.get("group", "default"),
            aff_code=user_info.get("aff_code"),
            aff_count=user_info.get("aff_count", 0),
            aff_history_quota=aff_history_quota,
            quota_display=format_quota(quota),
            used_quota_display=format_quota(used_quota),
            aff_history_quota_display=format_quota(aff_history_quota)
        )
    )


def sync_account_tokens(db: Session, account: Account) -> int:
    """
    同步账号的 API Tokens

    Returns:
        int: 同步的 token 数量
    """
    if not account.anyrouter_user_id:
        return 0

    success, result = anyrouter_service.get_tokens(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    if not success:
        return 0

    tokens = result.get("tokens", [])

    # 删除旧的 tokens
    db.query(ApiToken).filter(ApiToken.account_id == account.id).delete()

    # 添加新的 tokens
    for token_data in tokens:
        token = ApiToken(
            account_id=account.id,
            token_id=token_data.get("id"),
            key=token_data.get("key"),
            name=token_data.get("name"),
            status=token_data.get("status", 1),
            remain_quota=token_data.get("remain_quota", 0),
            used_quota=token_data.get("used_quota", 0),
            unlimited_quota=token_data.get("unlimited_quota", False),
            model_limits_enabled=token_data.get("model_limits_enabled", False),
            model_limits=token_data.get("model_limits"),
            created_time=token_data.get("created_time"),
            accessed_time=token_data.get("accessed_time"),
            expired_time=token_data.get("expired_time", -1),
            synced_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        db.add(token)

    db.commit()
    return len(tokens)


@router.get("/{account_id}/tokens", response_model=ApiResponse)
def get_account_tokens(account_id: int, db: Session = Depends(get_db)):
    """获取账号的 API Tokens"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    tokens = db.query(ApiToken).filter(ApiToken.account_id == account_id).all()

    return ApiResponse(
        success=True,
        data=[token.to_dict() for token in tokens]
    )


@router.post("/{account_id}/tokens/sync", response_model=ApiResponse)
def sync_tokens(account_id: int, db: Session = Depends(get_db)):
    """同步账号的 API Tokens"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    count = sync_account_tokens(db, account)

    return ApiResponse(
        success=True,
        message=f"同步完成，共 {count} 个 Token",
        data={"count": count}
    )
