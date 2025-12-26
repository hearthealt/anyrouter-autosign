"""
账号管理 API
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, AccountGroup, SignLog, NotifyChannel, AccountNotify, ApiToken
from app.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountInfo,
    LastSign, ApiResponse
)
from app.schemas.account import NotifyChannelBrief, HealthCheckResponse, GroupBrief, CreateTokenRequest
from app.services import anyrouter_service
from app.utils import format_quota, format_quota_percent

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


def get_group_brief(db: Session, group_id: Optional[int]) -> Optional[GroupBrief]:
    """获取分组简要信息"""
    if not group_id:
        return None
    group = db.query(AccountGroup).filter(AccountGroup.id == group_id).first()
    if not group:
        return None
    return GroupBrief(id=group.id, name=group.name, color=group.color or "default")


@router.get("", response_model=ApiResponse)
def get_accounts(db: Session = Depends(get_db)):
    """获取账号列表"""
    accounts = db.query(Account).order_by(Account.created_at.desc()).all()

    result = []
    for account in accounts:
        total_quota = account.cached_quota + account.cached_used_quota
        result.append(AccountResponse(
            id=account.id,
            username=account.username,
            display_name=account.display_name,
            anyrouter_user_id=account.anyrouter_user_id,
            is_active=account.is_active,
            created_at=account.created_at,
            updated_at=account.updated_at,
            notify_channels=get_account_notify_channels(db, account.id),
            last_sign=get_last_sign(db, account.id),
            health_status=account.health_status or "unknown",
            health_message=account.health_message,
            last_health_check=account.last_health_check,
            group_id=account.group_id,
            group=get_group_brief(db, account.group_id),
            cached_quota=account.cached_quota,
            cached_used_quota=account.cached_used_quota,
            quota_display=format_quota(account.cached_quota),
            quota_percent=format_quota_percent(account.cached_quota, total_quota)
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
        display_name=user_info.get("display_name"),
        health_status="healthy",
        last_health_check=datetime.now(),
        group_id=data.group_id,
        # 初始化所有缓存字段
        cached_quota=user_info.get("quota", 0),
        cached_used_quota=user_info.get("used_quota", 0),
        cached_request_count=user_info.get("request_count", 0),
        cached_user_group=user_info.get("group", "default"),
        cached_aff_code=user_info.get("aff_code"),
        cached_aff_count=user_info.get("aff_count", 0),
        cached_aff_history_quota=user_info.get("aff_history_quota", 0),
        quota_updated_at=datetime.now()
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
            last_sign=None,
            health_status=account.health_status,
            health_message=account.health_message,
            last_health_check=account.last_health_check
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
            last_sign=get_last_sign(db, account.id),
            health_status=account.health_status or "unknown",
            health_message=account.health_message,
            last_health_check=account.last_health_check
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
        # 更新所有缓存字段
        account.cached_quota = user_info.get("quota", 0)
        account.cached_used_quota = user_info.get("used_quota", 0)
        account.cached_request_count = user_info.get("request_count", 0)
        account.cached_user_group = user_info.get("group", "default")
        account.cached_aff_code = user_info.get("aff_code")
        account.cached_aff_count = user_info.get("aff_count", 0)
        account.cached_aff_history_quota = user_info.get("aff_history_quota", 0)
        account.quota_updated_at = datetime.now()

    if data.is_active is not None:
        account.is_active = data.is_active

    if data.group_id is not None:
        account.group_id = data.group_id if data.group_id > 0 else None

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
    """获取账号实时信息（会刷新缓存）"""
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
    request_count = user_info.get("request_count", 0)
    aff_history_quota = user_info.get("aff_history_quota", 0)

    # 更新所有缓存字段
    account.cached_quota = quota
    account.cached_used_quota = used_quota
    account.cached_request_count = request_count
    account.cached_user_group = user_info.get("group", "default")
    account.cached_aff_code = user_info.get("aff_code")
    account.cached_aff_count = user_info.get("aff_count", 0)
    account.cached_aff_history_quota = aff_history_quota
    account.quota_updated_at = datetime.now()
    # 同时更新用户名
    if user_info.get("username"):
        account.username = user_info.get("username")
    if user_info.get("display_name"):
        account.display_name = user_info.get("display_name")
    db.commit()

    # 获取本地分组信息
    local_group = None
    if account.group_id:
        group = db.query(AccountGroup).filter(AccountGroup.id == account.group_id).first()
        if group:
            local_group = GroupBrief(id=group.id, name=group.name, color=group.color or "default")

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
            request_count=request_count,
            group=user_info.get("group", "default"),
            aff_code=user_info.get("aff_code"),
            aff_count=user_info.get("aff_count", 0),
            aff_history_quota=aff_history_quota,
            quota_display=format_quota(quota),
            used_quota_display=format_quota(used_quota),
            quota_percent=format_quota_percent(quota, quota + used_quota),
            aff_history_quota_display=format_quota(aff_history_quota),
            group_id=account.group_id,
            local_group=local_group
        )
    )


@router.get("/{account_id}/cached-info", response_model=ApiResponse)
def get_cached_account_info(account_id: int, db: Session = Depends(get_db)):
    """获取账号缓存信息（不请求远程API，快速返回）"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    # 获取本地分组信息
    local_group = None
    if account.group_id:
        group = db.query(AccountGroup).filter(AccountGroup.id == account.group_id).first()
        if group:
            local_group = GroupBrief(id=group.id, name=group.name, color=group.color or "default")

    return ApiResponse(
        success=True,
        data=AccountInfo(
            id=account.anyrouter_user_id,
            username=account.username,
            display_name=account.display_name,
            role=0,
            status=1 if account.is_active else 0,
            quota=account.cached_quota,
            used_quota=account.cached_used_quota,
            request_count=account.cached_request_count,
            group=account.cached_user_group or "default",
            aff_code=account.cached_aff_code,
            aff_count=account.cached_aff_count,
            aff_history_quota=account.cached_aff_history_quota,
            quota_display=format_quota(account.cached_quota),
            used_quota_display=format_quota(account.cached_used_quota),
            quota_percent=format_quota_percent(account.cached_quota, account.cached_quota + account.cached_used_quota),
            aff_history_quota_display=format_quota(account.cached_aff_history_quota),
            group_id=account.group_id,
            local_group=local_group
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


def check_account_health(db: Session, account: Account) -> HealthCheckResponse:
    """
    检查单个账号的健康状态

    Args:
        db: 数据库会话
        account: 账号对象

    Returns:
        HealthCheckResponse: 健康检查结果
    """
    now = datetime.now()

    if not account.anyrouter_user_id:
        account.health_status = "unhealthy"
        account.health_message = "缺少 user_id"
        account.last_health_check = now
        db.commit()
        return HealthCheckResponse(
            account_id=account.id,
            health_status="unhealthy",
            health_message="缺少 user_id",
            checked_at=now
        )

    # 尝试获取用户信息来验证凭证
    success, user_info = anyrouter_service.get_user_info(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    if success:
        account.health_status = "healthy"
        account.health_message = None
        # 顺便更新用户名
        if user_info.get("username"):
            account.username = user_info.get("username")
        if user_info.get("display_name"):
            account.display_name = user_info.get("display_name")
        # 更新所有缓存字段
        account.cached_quota = user_info.get("quota", 0)
        account.cached_used_quota = user_info.get("used_quota", 0)
        account.cached_request_count = user_info.get("request_count", 0)
        account.cached_user_group = user_info.get("group", "default")
        account.cached_aff_code = user_info.get("aff_code")
        account.cached_aff_count = user_info.get("aff_count", 0)
        account.cached_aff_history_quota = user_info.get("aff_history_quota", 0)
        account.quota_updated_at = now
    else:
        account.health_status = "unhealthy"
        account.health_message = user_info.get("message", "凭证验证失败")

    account.last_health_check = now
    db.commit()

    return HealthCheckResponse(
        account_id=account.id,
        health_status=account.health_status,
        health_message=account.health_message,
        checked_at=now
    )


@router.post("/{account_id}/health-check", response_model=ApiResponse)
def health_check_account(account_id: int, db: Session = Depends(get_db)):
    """对单个账号执行健康检查"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    result = check_account_health(db, account)

    return ApiResponse(
        success=True,
        message=f"健康检查完成: {result.health_status}",
        data=result.model_dump()
    )


@router.post("/health-check/all", response_model=ApiResponse)
def health_check_all_accounts(db: Session = Depends(get_db)):
    """对所有启用的账号执行健康检查"""
    accounts = db.query(Account).filter(Account.is_active == True).all()

    results = []
    healthy_count = 0
    unhealthy_count = 0

    for account in accounts:
        result = check_account_health(db, account)
        results.append(result.model_dump())
        if result.health_status == "healthy":
            healthy_count += 1
        else:
            unhealthy_count += 1

    return ApiResponse(
        success=True,
        message=f"健康检查完成: {healthy_count} 个健康, {unhealthy_count} 个异常",
        data={
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "results": results
        }
    )


@router.post("/{account_id}/tokens", response_model=ApiResponse)
def create_account_token(account_id: int, data: CreateTokenRequest, db: Session = Depends(get_db)):
    """创建 API Token"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = anyrouter_service.create_token(
        session_cookie=account.session_cookie,
        user_id=str(account.anyrouter_user_id),
        name=data.name,
        remain_quota=data.remain_quota,
        expired_time=data.expired_time,
        unlimited_quota=data.unlimited_quota,
        model_limits_enabled=data.model_limits_enabled,
        model_limits=data.model_limits,
        allow_ips=data.allow_ips,
        group=data.group
    )

    if not success:
        raise HTTPException(status_code=400, detail=result.get("message", "创建令牌失败"))

    # 创建成功后同步 tokens
    sync_account_tokens(db, account)

    return ApiResponse(
        success=True,
        message=result.get("message", "创建成功")
    )


@router.get("/{account_id}/models", response_model=ApiResponse)
def get_account_models(account_id: int, db: Session = Depends(get_db)):
    """获取账号可用的模型列表"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = anyrouter_service.get_models(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    if not success:
        raise HTTPException(status_code=400, detail=result.get("message", "获取模型列表失败"))

    return ApiResponse(
        success=True,
        data=result.get("models", [])
    )


@router.get("/{account_id}/groups", response_model=ApiResponse)
def get_account_groups(account_id: int, db: Session = Depends(get_db)):
    """获取账号可用的分组列表（AnyRouter 平台分组）"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = anyrouter_service.get_groups(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    if not success:
        raise HTTPException(status_code=400, detail=result.get("message", "获取分组列表失败"))

    return ApiResponse(
        success=True,
        data=result.get("groups", {})
    )


@router.delete("/{account_id}/tokens/{token_id}", response_model=ApiResponse)
def delete_account_token(account_id: int, token_id: int, db: Session = Depends(get_db)):
    """删除 API Token"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    # 尝试远程删除
    success, result = anyrouter_service.delete_token(
        session_cookie=account.session_cookie,
        user_id=str(account.anyrouter_user_id),
        token_id=token_id
    )

    # 无论远程删除是否成功，都删除本地记录并同步
    # （远程可能已经删除了，或者网络问题等）
    db.query(ApiToken).filter(
        ApiToken.account_id == account_id,
        ApiToken.token_id == token_id
    ).delete()
    db.commit()

    # 同步令牌列表
    sync_account_tokens(db, account)

    if success:
        return ApiResponse(success=True, message="删除成功")
    else:
        # 远程删除失败但本地已清理，返回成功但提示
        return ApiResponse(success=True, message="本地已删除（远程可能已不存在）")


@router.put("/{account_id}/tokens/{token_id}", response_model=ApiResponse)
def update_account_token(account_id: int, token_id: int, data: dict, db: Session = Depends(get_db)):
    """更新 API Token"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    # 确保 token_data 包含必要字段
    data["id"] = token_id
    data["user_id"] = account.anyrouter_user_id

    success, result = anyrouter_service.update_token(
        session_cookie=account.session_cookie,
        user_id=str(account.anyrouter_user_id),
        token_data=data
    )

    if not success:
        # 更新失败，同步列表检查令牌是否还存在
        sync_account_tokens(db, account)
        # 检查本地是否还有这个令牌
        token_exists = db.query(ApiToken).filter(
            ApiToken.account_id == account_id,
            ApiToken.token_id == token_id
        ).first()

        if not token_exists:
            # 远程已删除
            raise HTTPException(
                status_code=400,
                detail="更新失败：该令牌在远程已不存在，本地已同步清理"
            )
        else:
            # 其他原因失败（网络等）
            raise HTTPException(
                status_code=400,
                detail=result.get("message", "更新令牌失败")
            )

    # 更新成功后同步 tokens
    sync_account_tokens(db, account)

    return ApiResponse(
        success=True,
        message=result.get("message", "更新成功")
    )
