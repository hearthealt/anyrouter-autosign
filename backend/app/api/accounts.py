"""
账号管理 API
"""
from datetime import datetime
import json
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import String, asc, case, cast, desc, func, or_
from sqlalchemy.orm import Query, Session

from app.database import get_db
from app.models import Account, AccountGroup, SignLog, NotifyChannel, AccountNotify, ApiToken, User, AuditAction, Platform
from app.schemas import (
    AccountCreate, AccountUpdate, AccountResponse, AccountInfo,
    LastSign, ApiResponse, BatchImportRequest, BatchImportResultItem
)
from app.schemas.account import NotifyChannelBrief, HealthCheckResponse, GroupBrief, CreateTokenRequest, PlatformBrief
from app.services import (
    anrouter_service,
    build_transient_credential,
    execute_with_session_refresh,
    has_login_credentials,
    load_auth_data,
    refresh_account_user_cache,
    resolve_session_cookie,
)
from app.services.adapters import adapter_registry
from app.services.audit import log_action
from app.services.events import publish_event
from app.services.newapi_credentials import (
    ROTATE_KEY_ACCESS_EXPIRES_AT,
    ROTATE_KEY_ACCESS_TOKEN,
    ROTATE_KEY_REFRESH_TOKEN,
    SCHEME_REFRESH,
    decode_access_token_expiry,
)
from app.utils import (
    format_quota,
    format_quota_percent,
    get_platform_config,
    get_account_platform_config,
    mask_proxy_url,
    normalize_proxy_mode,
    normalize_proxy_url,
    validate_proxy_url,
)
from app.utils.platform import ADAPTER_TYPE_HTTP, ADAPTER_TYPE_NEW_API
from app.api.deps import get_current_user

router = APIRouter(prefix="/accounts", tags=["账号管理"])


def get_platform_by_id(db: Session, platform_id: Optional[int]) -> Optional[Platform]:
    """按 ID 获取平台。"""
    if not platform_id:
        return None
    return db.query(Platform).filter(Platform.id == platform_id).first()


def ensure_account_platform(account: Account) -> Platform:
    """确保账号已绑定平台。"""
    if not account.platform_id or not account.platform:
        raise HTTPException(status_code=400, detail="账号未配置平台")
    return account.platform


def find_existing_account(
    db: Session,
    platform_id: Optional[int],
    *,
    external_user_id: Optional[str] = None,
    anyrouter_user_id: Optional[int] = None,
    exclude_account_id: Optional[int] = None,
) -> Optional[Account]:
    """按平台及外部账号标识查找重复账号。"""
    query = db.query(Account)
    if exclude_account_id is not None:
        query = query.filter(Account.id != exclude_account_id)
    if platform_id is None:
        query = query.filter(Account.platform_id.is_(None))
    else:
        query = query.filter(Account.platform_id == platform_id)

    if anyrouter_user_id is not None:
        return query.filter(Account.anyrouter_user_id == anyrouter_user_id).first()
    cleaned_external_id = clean_optional_str(external_user_id)
    if cleaned_external_id:
        return query.filter(Account.external_user_id == cleaned_external_id).first()
    return None


def get_account_platform(account: Account) -> Optional[PlatformBrief]:
    """获取账号的平台简要信息"""
    if account.platform_id and account.platform:
        return PlatformBrief(
            id=account.platform.id,
            name=account.platform.name,
            base_url=account.platform.base_url,
            adapter_type=account.platform.adapter_type or ADAPTER_TYPE_NEW_API,
        )
    return None


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


def clean_optional_str(value: Optional[str]) -> Optional[str]:
    """清理可选字符串输入。"""
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def clean_optional_secret(value: Optional[str]) -> Optional[str]:
    """保留密码原始内容，仅将空串视为未填写。"""
    if value is None:
        return None
    return value if value != "" else None


def clean_optional_note(value: Optional[str]) -> Optional[str]:
    """清理备注字段并限制长度。"""
    cleaned = clean_optional_str(value)
    if not cleaned:
        return None
    return cleaned[:255]


def clean_account_proxy(proxy_mode: Optional[str], proxy_url: Optional[str]) -> Tuple[str, Optional[str]]:
    """校验并清理账号级代理配置。"""
    mode = normalize_proxy_mode(proxy_mode)
    cleaned_proxy_url = normalize_proxy_url(proxy_url)
    if mode == "custom":
        if not cleaned_proxy_url:
            raise HTTPException(status_code=400, detail="自定义代理模式必须填写代理地址")
        validate_proxy_url(cleaned_proxy_url)
        return mode, cleaned_proxy_url
    return mode, None


VALID_AUTH_TYPES = {"none", "custom", "bearer", "cookie", "header", "basic", SCHEME_REFRESH}
MAX_AUTH_DATA_LENGTH = 64 * 1024


def normalize_auth_type(value: Optional[str], *, has_session_cookie: bool = False) -> str:
    auth_type = (value or ("cookie" if has_session_cookie else "none")).strip().lower()
    if auth_type not in VALID_AUTH_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的认证方式: {auth_type}")
    return auth_type


def serialize_auth_data(value: Optional[Dict[str, Any]]) -> tuple[Dict[str, Any], Optional[str]]:
    auth_data = dict(value or {})
    try:
        serialized = json.dumps(auth_data, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="认证数据必须是可序列化的 JSON 对象") from exc
    if len(serialized.encode("utf-8")) > MAX_AUTH_DATA_LENGTH:
        raise HTTPException(status_code=400, detail="认证数据不能超过 64KB")
    return auth_data, serialized if auth_data else None


def prepare_http_auth(
    auth_type_value: Optional[str],
    auth_data_value: Optional[Dict[str, Any]],
    session_cookie: Optional[str],
) -> tuple[str, Optional[str]]:
    auth_data = dict(auth_data_value or {})
    auth_type = normalize_auth_type(auth_type_value, has_session_cookie=bool(session_cookie))
    if auth_type == "cookie" and session_cookie and not auth_data.get("cookie") and not auth_data.get("cookies"):
        auth_data["cookie"] = session_cookie

    if auth_type == "bearer" and not clean_optional_secret(auth_data.get("token")):
        raise HTTPException(status_code=400, detail="Bearer 认证需要 auth_data.token")
    if auth_type == SCHEME_REFRESH and not clean_optional_secret(auth_data.get(ROTATE_KEY_REFRESH_TOKEN)):
        raise HTTPException(status_code=400, detail="Refresh 认证需要 auth_data.refresh_token")
    if auth_type == "cookie" and not (auth_data.get("cookie") or isinstance(auth_data.get("cookies"), dict)):
        raise HTTPException(status_code=400, detail="Cookie 认证需要 Session Cookie、auth_data.cookie 或 auth_data.cookies")
    if auth_type == "header" and not (isinstance(auth_data.get("headers"), dict) or auth_data.get("name")):
        raise HTTPException(status_code=400, detail="Header 认证需要 auth_data.headers 或 name/value")
    if auth_type == "basic" and (auth_data.get("username") is None or auth_data.get("password") is None):
        raise HTTPException(status_code=400, detail="Basic 认证需要 auth_data.username 和 auth_data.password")

    _, serialized = serialize_auth_data(auth_data)
    return auth_type, serialized


def prepare_new_api_auth(
    auth_type_value: Optional[str],
    auth_data_value: Optional[Dict[str, Any]],
) -> tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """解析 new_api 平台的面板凭证。

    新版 new-api 支持两种可直接使用的凭证：系统访问令牌（PAT，永不过期）和
    ``new_api_refresh`` cookie（每次刷新都会轮换）。未指定时返回 ``(None, None, {})``，
    走旧的 ``session`` cookie 方案，行为与改造前一致。

    :return: ``(auth_type, serialized_auth_data, auth_data_dict)``
    """
    auth_type = (auth_type_value or "").strip().lower()
    incoming = dict(auth_data_value or {})

    if auth_type == "bearer":
        token = clean_optional_secret(incoming.get("token"))
        if not token:
            raise HTTPException(status_code=400, detail="系统访问令牌认证需要 auth_data.token")
        auth_data = {"token": token}
    elif auth_type == SCHEME_REFRESH:
        refresh_token = clean_optional_secret(incoming.get(ROTATE_KEY_REFRESH_TOKEN))
        if not refresh_token:
            raise HTTPException(status_code=400, detail="Refresh 认证需要 auth_data.refresh_token")
        auth_data = {ROTATE_KEY_REFRESH_TOKEN: refresh_token}
        # 允许一并粘贴当前 access_token，省掉首次刷新
        access_token = clean_optional_secret(incoming.get(ROTATE_KEY_ACCESS_TOKEN))
        if access_token:
            auth_data[ROTATE_KEY_ACCESS_TOKEN] = access_token
            auth_data[ROTATE_KEY_ACCESS_EXPIRES_AT] = decode_access_token_expiry(access_token)
    elif auth_type in ("", "none", "cookie"):
        return None, None, {}
    else:
        raise HTTPException(status_code=400, detail=f"New API 平台不支持的认证方式: {auth_type}")

    _, serialized = serialize_auth_data(auth_data)
    return auth_type, serialized, auth_data


def get_platform_adapter(platform_config: Dict[str, Any]):
    return adapter_registry.get(platform_config["adapter_type"])


def require_adapter_capability(account: Account, capability: str, feature_name: str) -> Dict[str, Any]:
    ensure_account_platform(account)
    platform_config = get_account_platform_config(account)
    adapter = get_platform_adapter(platform_config)
    if not getattr(adapter.capabilities, capability, False):
        raise HTTPException(status_code=400, detail=f"当前平台适配器不支持{feature_name}")
    return platform_config


def _create_account_record(db: Session, data: Any) -> Account:
    platform = get_platform_by_id(db, data.platform_id)
    if not platform:
        raise HTTPException(status_code=400, detail="平台不存在")
    platform_config = get_platform_config(platform)
    adapter = get_platform_adapter(platform_config)
    note = clean_optional_note(data.note)
    proxy_mode, proxy_url = clean_account_proxy(data.proxy_mode, data.proxy_url)

    if platform_config["adapter_type"] == ADAPTER_TYPE_HTTP:
        session_cookie = clean_optional_str(data.session_cookie)
        external_user_id = clean_optional_str(data.external_user_id or data.user_id)
        auth_type, auth_data = prepare_http_auth(data.auth_type, data.auth_data, session_cookie)
        if find_existing_account(db, platform.id, external_user_id=external_user_id):
            raise HTTPException(status_code=400, detail="该平台下该外部账号标识已存在")

        account = Account(
            session_cookie=session_cookie or "",
            external_user_id=external_user_id,
            auth_type=auth_type,
            auth_data=auth_data,
            username=clean_optional_str(data.username) or external_user_id or f"{platform.name} 账号",
            display_name=clean_optional_str(data.display_name),
            note=note,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
            health_status="unknown",
            health_message="通用 HTTP 适配器未配置独立健康检查",
            platform_id=platform.id,
            group_id=data.group_id,
        )
    else:
        user_id = clean_optional_str(data.user_id or data.external_user_id)
        session_cookie = clean_optional_str(data.session_cookie)
        login_username = clean_optional_str(data.login_username)
        login_password = clean_optional_secret(data.login_password)
        new_api_auth_type, new_api_auth_data, auth_data_dict = prepare_new_api_auth(
            data.auth_type, data.auth_data
        )
        if bool(login_username) != bool(login_password):
            raise HTTPException(status_code=400, detail="登录账号和密码需要同时填写")
        # User ID 只在手填 Session Cookie 时是必需的 —— cookie 本身不带身份，
        # 旧版 new-api 要靠 new-api-user 头。其余方式都能从服务端拿到 ID：
        # 登录响应带 data.id / data.user.id，PAT 和 refresh 令牌本身就携带身份。
        if not new_api_auth_type and not (login_username and login_password) and not (user_id and session_cookie):
            raise HTTPException(
                status_code=400,
                detail="请填写登录账号和密码，或提供系统访问令牌 / refresh token，或同时填写 User ID 和 Session Cookie",
            )

        if new_api_auth_type:
            # 直接给了 PAT 或 refresh token：不需要 session cookie，也不需要先登录
            session_result: Dict[str, Any] = {}
        else:
            resolved, session_result = resolve_session_cookie(
                base_url=platform_config["base_url"],
                session_cookie=session_cookie,
                login_username=login_username,
                login_password=login_password,
                prefer_login=not user_id and bool(login_username and login_password),
                proxy_mode=proxy_mode,
                proxy_url=proxy_url,
            )
            if not resolved:
                raise HTTPException(status_code=400, detail=session_result.get("message", "凭证解析失败"))
            # 登录时若识别为新版方案，改走 refresh 凭证而不是 session cookie
            if session_result.get("auth_scheme") == SCHEME_REFRESH:
                new_api_auth_type = SCHEME_REFRESH
                auth_data_dict = {
                    ROTATE_KEY_REFRESH_TOKEN: session_result.get(ROTATE_KEY_REFRESH_TOKEN) or "",
                    ROTATE_KEY_ACCESS_TOKEN: session_result.get(ROTATE_KEY_ACCESS_TOKEN) or "",
                    ROTATE_KEY_ACCESS_EXPIRES_AT: int(session_result.get(ROTATE_KEY_ACCESS_EXPIRES_AT) or 0),
                }
                _, new_api_auth_data = serialize_auth_data(auth_data_dict)
            if not user_id:
                user_id = clean_optional_str(session_result.get("user_id"))

        # 校验 refresh 凭证会让服务端当场轮换，必须把轮换后的新值收下来落库
        rotated: Dict[str, Any] = {}
        credential = build_transient_credential(
            platform_config["base_url"],
            new_api_auth_type,
            auth_data_dict,
            session_result.get("session_cookie", ""),
            user_id=user_id or None,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
            on_rotate=rotated.update,
        )
        success, user_info = anrouter_service.get_user_info(
            credential,
            user_id or "",
            platform_config["base_url"],
            user_api=platform_config["user_api"],
            console_url=platform_config["console_url"],
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
        if not success:
            raise HTTPException(status_code=400, detail=user_info.get("message", "验证失败"))

        # 令牌方案走到这里才知道 User ID：从校验响应里回填
        if not user_id:
            resolved_id = user_info.get("id")
            user_id = clean_optional_str(str(resolved_id)) if resolved_id is not None else None
        try:
            numeric_user_id = int(user_id or "")
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="未能从平台确定 User ID，请手动填写",
            ) from exc

        if find_existing_account(db, platform.id, anyrouter_user_id=numeric_user_id):
            raise HTTPException(status_code=400, detail="该平台下该账号已存在")

        if rotated:
            auth_data_dict.update(rotated)
            _, new_api_auth_data = serialize_auth_data(auth_data_dict)

        now = datetime.now()
        account = Account(
            session_cookie=session_result.get("session_cookie", ""),
            login_username=login_username,
            login_password=login_password,
            anyrouter_user_id=numeric_user_id,
            external_user_id=str(numeric_user_id),
            auth_type=new_api_auth_type,
            auth_data=new_api_auth_data,
            username=user_info.get("username"),
            display_name=user_info.get("display_name"),
            note=note,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
            health_status="healthy",
            last_health_check=now,
            platform_id=platform.id,
            group_id=data.group_id,
            cached_quota=user_info.get("quota", 0),
            cached_used_quota=user_info.get("used_quota", 0),
            cached_request_count=user_info.get("request_count", 0),
            cached_user_group=user_info.get("group", "default"),
            cached_aff_code=user_info.get("aff_code"),
            cached_aff_count=user_info.get("aff_count", 0),
            cached_aff_history_quota=user_info.get("aff_history_quota", 0),
            quota_updated_at=now,
        )

    db.add(account)
    db.commit()
    db.refresh(account)
    if adapter.capabilities.supports_tokens:
        sync_account_tokens(db, account)
    return account


def build_account_response(db: Session, account: Account) -> AccountResponse:
    """统一构造账号响应。"""
    total_quota = account.cached_quota + account.cached_used_quota
    return AccountResponse(
        id=account.id,
        username=account.username,
        display_name=account.display_name,
        note=account.note,
        login_username=account.login_username,
        has_login_credentials=has_login_credentials(account),
        external_user_id=account.external_user_id,
        auth_type=account.auth_type,
        has_auth_data=bool(account.auth_data),
        proxy_mode=account.proxy_mode or "direct",
        proxy_url=None,
        proxy_url_masked=mask_proxy_url(account.proxy_url) if account.proxy_url else None,
        anrouter_user_id=account.anrouter_user_id,
        anyrouter_user_id=account.anyrouter_user_id,
        is_active=account.is_active,
        created_at=account.created_at,
        updated_at=account.updated_at,
        platform=get_account_platform(account),
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
    )


def build_accounts_query(
    db: Session,
    keyword: Optional[str] = None,
    platform_id: Optional[int] = None,
    group_id: Optional[int] = None
) -> Tuple[Query, Query]:
    """构造账号列表基础查询。"""
    last_sign_subquery = db.query(
        SignLog.account_id.label("account_id"),
        func.max(SignLog.sign_time).label("last_sign_time")
    ).group_by(SignLog.account_id).subquery()

    query = db.query(Account).outerjoin(
        Platform, Platform.id == Account.platform_id
    ).outerjoin(
        AccountGroup, AccountGroup.id == Account.group_id
    ).outerjoin(
        last_sign_subquery, last_sign_subquery.c.account_id == Account.id
    )

    cleaned_keyword = clean_optional_str(keyword)
    if cleaned_keyword:
        like_pattern = f"%{cleaned_keyword}%"
        query = query.filter(or_(
            Account.username.ilike(like_pattern),
            Account.display_name.ilike(like_pattern),
            Account.note.ilike(like_pattern),
            Platform.name.ilike(like_pattern),
            Account.external_user_id.ilike(like_pattern),
            cast(Account.anyrouter_user_id, String).ilike(like_pattern)
        ))

    if platform_id is not None:
        query = query.filter(Account.platform_id == platform_id)

    if group_id is not None:
        query = query.filter(Account.group_id == group_id)

    return query, last_sign_subquery


def apply_account_status_filter(
    query: Query,
    status: Optional[str],
    last_sign_subquery: Query,
    today_start: datetime
) -> Query:
    """应用账号状态筛选。"""
    if not status:
        return query

    if status == "normal":
        # 正常包含已启用且当前没有异常标记的账号；unknown/未检查不再单独作为账号状态。
        return query.filter(
            Account.is_active == True,
            or_(
                Account.health_status != "unhealthy",
                Account.health_status.is_(None),
            ),
        )
    if status == "healthy":
        # 兼容旧客户端的筛选参数。
        return query.filter(Account.is_active == True, Account.health_status == "healthy")
    if status == "unhealthy":
        return query.filter(Account.is_active == True, Account.health_status == "unhealthy")
    if status == "pending":
        return query.filter(
            Account.is_active == True,
            or_(
                last_sign_subquery.c.last_sign_time.is_(None),
                last_sign_subquery.c.last_sign_time < today_start
            )
        )
    if status == "disabled":
        return query.filter(Account.is_active == False)

    return query


def build_accounts_summary(
    base_query: Query,
    last_sign_subquery: Query,
    today_start: datetime
) -> dict:
    """构造账号列表汇总信息。"""
    summary_query = base_query.order_by(None)
    active_query = summary_query.filter(Account.is_active == True)

    active_count = active_query.count()
    unhealthy_count = active_query.filter(Account.health_status == "unhealthy").count()

    return {
        "total": summary_query.count(),
        "active_count": active_count,
        # 三种账号状态：正常、异常、禁用。正常优先覆盖 unknown/未检查。
        "normal_count": active_count - unhealthy_count,
        # 保留旧字段，避免旧客户端读取摘要时出现兼容问题。
        "healthy_count": active_query.filter(Account.health_status == "healthy").count(),
        "unhealthy_count": unhealthy_count,
        "disabled_count": summary_query.filter(Account.is_active == False).count(),
        "pending_count": active_query.filter(or_(
            last_sign_subquery.c.last_sign_time.is_(None),
            last_sign_subquery.c.last_sign_time < today_start
        )).count()
    }


def apply_account_sort(
    query: Query,
    sort_by: Optional[str],
    sort_order: str,
    last_sign_subquery: Query
) -> Query:
    """应用账号列表排序。"""
    normalized_order = (sort_order or "desc").lower()
    is_desc = normalized_order.startswith("desc")

    if not sort_by:
        return query.order_by(Account.created_at.desc(), Account.id.desc())

    if sort_by == "username":
        sort_column = Account.username
    elif sort_by == "platform":
        sort_column = Platform.name
    elif sort_by == "group":
        sort_column = AccountGroup.name
    elif sort_by == "quota":
        sort_column = Account.cached_quota
    elif sort_by == "last_sign":
        sort_column = last_sign_subquery.c.last_sign_time
        null_rank = case((last_sign_subquery.c.last_sign_time.is_(None), 1), else_=0)
        return query.order_by(
            null_rank.asc(),
            desc(sort_column) if is_desc else asc(sort_column),
            Account.id.desc()
        )
    elif sort_by == "health":
        sort_column = case(
            (Account.is_active == False, 0),
            (Account.health_status == "unhealthy", 1),
            else_=2,
        )
    else:
        return query.order_by(Account.created_at.desc(), Account.id.desc())

    return query.order_by(desc(sort_column) if is_desc else asc(sort_column), Account.id.desc())


@router.get("", response_model=ApiResponse)
def get_accounts(
    page: Optional[int] = None,
    size: Optional[int] = None,
    keyword: Optional[str] = None,
    platform_id: Optional[int] = None,
    group_id: Optional[int] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """获取账号列表"""
    base_query, last_sign_subquery = build_accounts_query(
        db=db,
        keyword=keyword,
        platform_id=platform_id,
        group_id=group_id
    )

    if all(param is None for param in (page, size, keyword, platform_id, group_id, status, sort_by)):
        accounts = base_query.order_by(Account.created_at.desc()).all()
        return ApiResponse(success=True, data=[build_account_response(db, account) for account in accounts])

    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    summary = build_accounts_summary(base_query, last_sign_subquery, today_start)
    filtered_query = apply_account_status_filter(base_query, status, last_sign_subquery, today_start)
    total = filtered_query.order_by(None).count()

    resolved_page = max(page or 1, 1)
    resolved_size = min(max(size or 10, 1), 100)
    accounts = apply_account_sort(
        filtered_query,
        sort_by=sort_by,
        sort_order=sort_order,
        last_sign_subquery=last_sign_subquery
    ).offset((resolved_page - 1) * resolved_size).limit(resolved_size).all()

    return ApiResponse(
        success=True,
        data={
            "items": [build_account_response(db, account) for account in accounts],
            "total": total,
            "page": resolved_page,
            "size": resolved_size,
            "summary": summary
        }
    )


@router.post("", response_model=ApiResponse)
def create_account(
    data: AccountCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加 New API 或通用 HTTP 平台账号。"""
    account = _create_account_record(db, data)
    log_action(
        db=db,
        action=AuditAction.ACCOUNT_CREATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="account",
        target_id=account.id,
        target_name=account.username,
        request=request,
    )
    publish_event("account_changed", {
        "account_id": account.id,
        "username": account.username or "",
        "action": "created",
    })
    return ApiResponse(success=True, message="账号添加成功", data=build_account_response(db, account))


@router.post("/batch-import", response_model=ApiResponse)
def batch_import_accounts(
    data: BatchImportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """批量导入账号；每条按所属平台适配器独立验证。"""
    results: List[BatchImportResultItem] = []
    success_count = 0
    for idx, item in enumerate(data.items):
        try:
            account = _create_account_record(db, item)
            log_action(
                db=db,
                action=AuditAction.ACCOUNT_CREATE,
                user_id=current_user.id,
                username=current_user.username,
                target_type="account",
                target_id=account.id,
                target_name=account.username,
                request=request,
            )
            publish_event("account_changed", {
                "account_id": account.id,
                "username": account.username or "",
                "action": "created",
            })
            success_count += 1
            results.append(BatchImportResultItem(
                index=idx, success=True, message="导入成功",
                account_id=account.id, username=account.username,
            ))
        except HTTPException as exc:
            db.rollback()
            results.append(BatchImportResultItem(index=idx, success=False, message=str(exc.detail)))
        except Exception as exc:
            db.rollback()
            results.append(BatchImportResultItem(index=idx, success=False, message=str(exc) or "导入失败"))

    return ApiResponse(
        success=True,
        message=f"批量导入完成：成功 {success_count}，失败 {len(data.items) - success_count}",
        data={
            "total": len(data.items),
            "success_count": success_count,
            "fail_count": len(data.items) - success_count,
            "results": [result.model_dump() for result in results],
        },
    )


@router.get("/{account_id}", response_model=ApiResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取账号详情"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    return ApiResponse(success=True, data=build_account_response(db, account))


# 只落本地库、不依赖平台凭证的字段
LOCAL_ONLY_UPDATE_FIELDS = {"is_active", "group_id", "note"}


def apply_local_account_fields(account: Account, updates: Dict[str, Any]) -> Dict[str, Any]:
    """应用不依赖平台凭证的本地字段，返回审计用的变更摘要。"""
    changes: Dict[str, Any] = {}
    if "is_active" in updates:
        account.is_active = bool(updates["is_active"])
        changes["is_active"] = "已启用" if account.is_active else "已禁用"
    if "group_id" in updates:
        group_id = updates["group_id"]
        account.group_id = group_id if group_id and group_id > 0 else None
        changes["group_id"] = account.group_id
    if "note" in updates:
        account.note = clean_optional_note(updates.get("note"))
        changes["note"] = "已更新"
    return changes


@router.put("/{account_id}", response_model=ApiResponse)
def update_account(
    account_id: int,
    data: AccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """按目标平台适配器更新账号。"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    updates = data.model_dump(exclude_unset=True)

    # 只调整本地状态（禁用/分组/备注）时不回平台校验凭证：凭证已失效的账号也要能禁用。
    # 启用账号会走下面的完整流程，仍然确认凭证可用。
    if updates and set(updates) <= LOCAL_ONLY_UPDATE_FIELDS and updates.get("is_active") is not True:
        local_changes = apply_local_account_fields(account, updates)
        account.updated_at = datetime.now()
        db.commit()
        db.refresh(account)

        log_action(
            db=db, action=AuditAction.ACCOUNT_UPDATE, user_id=current_user.id,
            username=current_user.username, target_type="account", target_id=account.id,
            target_name=account.username, detail=local_changes or None, request=request,
        )
        publish_event("account_changed", {
            "account_id": account.id, "username": account.username or "", "action": "updated",
        })
        return ApiResponse(success=True, message="账号更新成功", data=build_account_response(db, account))

    target_platform_id = updates.get("platform_id", account.platform_id)
    target_platform = get_platform_by_id(db, target_platform_id)
    if not target_platform:
        raise HTTPException(status_code=400, detail="账号未配置有效平台")
    platform_config = get_platform_config(target_platform)
    adapter = get_platform_adapter(platform_config)
    changes: Dict[str, Any] = {}

    proxy_mode = updates.get("proxy_mode", account.proxy_mode or "direct")
    proxy_url = updates.get("proxy_url", account.proxy_url)
    if proxy_mode == "custom" and updates.get("proxy_url") == "" and account.proxy_url:
        proxy_url = account.proxy_url
    proxy_mode, proxy_url = clean_account_proxy(proxy_mode, proxy_url)

    if platform_config["adapter_type"] == ADAPTER_TYPE_HTTP:
        external_user_id = clean_optional_str(
            updates.get("external_user_id", updates.get("user_id", account.external_user_id))
        )
        if find_existing_account(
            db, target_platform.id, external_user_id=external_user_id, exclude_account_id=account.id
        ):
            raise HTTPException(status_code=400, detail="该平台下该外部账号标识已存在")

        session_cookie = account.session_cookie
        if "session_cookie" in updates:
            session_cookie = clean_optional_str(updates.get("session_cookie"))
        if updates.get("clear_auth_data"):
            auth_type = "none"
            auth_data = None
        elif "auth_data" in updates or "auth_type" in updates or "session_cookie" in updates:
            current_auth_data = None
            if "auth_data" not in updates and account.auth_data:
                try:
                    current_auth_data = json.loads(account.auth_data)
                except (TypeError, ValueError):
                    current_auth_data = {}
            auth_type, auth_data = prepare_http_auth(
                updates.get("auth_type", account.auth_type),
                updates.get("auth_data", current_auth_data),
                session_cookie,
            )
        else:
            auth_type, auth_data = account.auth_type or "none", account.auth_data

        account.platform_id = target_platform.id
        account.session_cookie = session_cookie or ""
        account.external_user_id = external_user_id
        account.auth_type = auth_type
        account.auth_data = auth_data
        account.anyrouter_user_id = None
        account.username = clean_optional_str(updates.get("username", account.username)) or external_user_id or f"{target_platform.name} 账号"
        if "display_name" in updates:
            account.display_name = clean_optional_str(updates.get("display_name"))
        if updates.get("clear_login_credentials"):
            account.login_username = None
            account.login_password = None
        account.health_status = "unknown"
        account.health_message = "通用 HTTP 适配器未配置独立健康检查"
        account.last_health_check = datetime.now()
        db.query(ApiToken).filter(ApiToken.account_id == account.id).delete()
        changes["credentials"] = "已更新"
    else:
        user_id_value = clean_optional_str(
            updates.get("user_id", updates.get("external_user_id", str(account.anyrouter_user_id or "")))
        )
        login_username = clean_optional_str(updates.get("login_username", account.login_username))
        login_password = clean_optional_secret(updates.get("login_password", account.login_password))
        if updates.get("clear_login_credentials"):
            login_username = None
            login_password = None
        if bool(login_username) != bool(login_password):
            raise HTTPException(status_code=400, detail="登录账号和密码需要同时填写")

        prefer_login = "login_username" in updates or "login_password" in updates

        # 解析面板凭证：显式清除 → 回落 session cookie；未提及 → 保持原样
        if updates.get("clear_auth_data"):
            new_api_auth_type, new_api_auth_data, auth_data_dict = None, None, {}
        elif "auth_type" in updates or "auth_data" in updates:
            current_auth_data = load_auth_data(account) if "auth_data" not in updates else None
            new_api_auth_type, new_api_auth_data, auth_data_dict = prepare_new_api_auth(
                updates.get("auth_type", account.auth_type),
                updates.get("auth_data", current_auth_data),
            )
        else:
            new_api_auth_type = account.auth_type
            new_api_auth_data = account.auth_data
            auth_data_dict = load_auth_data(account)

        if new_api_auth_type and not prefer_login:
            # 已有 PAT / refresh token，不需要 session cookie 也不需要登录
            session_result: Dict[str, Any] = {}
        else:
            resolved, session_result = resolve_session_cookie(
                base_url=platform_config["base_url"],
                session_cookie=clean_optional_str(updates.get("session_cookie", account.session_cookie)),
                login_username=login_username,
                login_password=login_password,
                prefer_login=prefer_login,
                proxy_mode=proxy_mode,
                proxy_url=proxy_url,
            )
            if not resolved:
                raise HTTPException(status_code=400, detail=session_result.get("message", "凭证验证失败"))
            if session_result.get("auth_scheme") == SCHEME_REFRESH:
                new_api_auth_type = SCHEME_REFRESH
                auth_data_dict = {
                    ROTATE_KEY_REFRESH_TOKEN: session_result.get(ROTATE_KEY_REFRESH_TOKEN) or "",
                    ROTATE_KEY_ACCESS_TOKEN: session_result.get(ROTATE_KEY_ACCESS_TOKEN) or "",
                    ROTATE_KEY_ACCESS_EXPIRES_AT: int(session_result.get(ROTATE_KEY_ACCESS_EXPIRES_AT) or 0),
                }
                _, new_api_auth_data = serialize_auth_data(auth_data_dict)
            if not user_id_value:
                user_id_value = clean_optional_str(session_result.get("user_id"))

        rotated: Dict[str, Any] = {}
        credential = build_transient_credential(
            platform_config["base_url"],
            new_api_auth_type,
            auth_data_dict,
            session_result.get("session_cookie", ""),
            user_id=user_id_value or None,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
            on_rotate=rotated.update,
        )
        success, user_info = anrouter_service.get_user_info(
            credential,
            user_id_value or "",
            platform_config["base_url"],
            user_api=platform_config["user_api"],
            console_url=platform_config["console_url"],
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )
        if not success:
            raise HTTPException(status_code=400, detail=user_info.get("message", "凭证验证失败"))

        # 令牌方案走到这里才知道 User ID：从校验响应里回填
        if not user_id_value:
            resolved_id = user_info.get("id")
            user_id_value = clean_optional_str(str(resolved_id)) if resolved_id is not None else None
        try:
            numeric_user_id = int(user_id_value or "")
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail="未能从平台确定 User ID，请手动填写") from exc
        if find_existing_account(
            db, target_platform.id, anyrouter_user_id=numeric_user_id, exclude_account_id=account.id
        ):
            raise HTTPException(status_code=400, detail="该平台下该账号已存在")

        if rotated:
            auth_data_dict.update(rotated)
            _, new_api_auth_data = serialize_auth_data(auth_data_dict)

        account.platform_id = target_platform.id
        account.session_cookie = session_result.get("session_cookie", "")
        account.login_username = login_username
        account.login_password = login_password
        account.anyrouter_user_id = numeric_user_id
        account.external_user_id = str(numeric_user_id)
        account.auth_type = new_api_auth_type
        account.auth_data = new_api_auth_data
        account.username = user_info.get("username")
        account.display_name = user_info.get("display_name")
        account.cached_quota = user_info.get("quota", 0)
        account.cached_used_quota = user_info.get("used_quota", 0)
        account.cached_request_count = user_info.get("request_count", 0)
        account.cached_user_group = user_info.get("group", "default")
        account.cached_aff_code = user_info.get("aff_code")
        account.cached_aff_count = user_info.get("aff_count", 0)
        account.cached_aff_history_quota = user_info.get("aff_history_quota", 0)
        account.quota_updated_at = datetime.now()
        account.health_status = "healthy"
        account.health_message = None
        account.last_health_check = datetime.now()
        changes["credentials"] = "已更新"

    account.proxy_mode = proxy_mode
    account.proxy_url = proxy_url
    changes.update(apply_local_account_fields(account, updates))
    account.updated_at = datetime.now()
    db.commit()
    db.refresh(account)
    if adapter.capabilities.supports_tokens:
        sync_account_tokens(db, account)

    log_action(
        db=db, action=AuditAction.ACCOUNT_UPDATE, user_id=current_user.id,
        username=current_user.username, target_type="account", target_id=account.id,
        target_name=account.username, detail=changes or None, request=request,
    )
    publish_event("account_changed", {
        "account_id": account.id, "username": account.username or "", "action": "updated",
    })
    return ApiResponse(success=True, message="账号更新成功", data=build_account_response(db, account))


@router.delete("/{account_id}", response_model=ApiResponse)
def delete_account(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除账号"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    account_name = account.username

    # 删除关联的推送配置
    db.query(AccountNotify).filter(AccountNotify.account_id == account_id).delete()

    # 删除签到日志
    db.query(SignLog).filter(SignLog.account_id == account_id).delete()

    # 删除账号
    db.delete(account)
    db.commit()

    # 记录审计日志
    log_action(
        db=db,
        action=AuditAction.ACCOUNT_DELETE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="account",
        target_id=account_id,
        target_name=account_name,
        request=request
    )

    publish_event(
        "account_changed",
        {
            "account_id": account_id,
            "username": account_name or "",
            "action": "deleted",
        }
    )

    return ApiResponse(success=True, message="账号删除成功")


@router.get("/{account_id}/info", response_model=ApiResponse)
def get_account_info(account_id: int, db: Session = Depends(get_db)):
    """获取账号实时信息（会刷新缓存）"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    platform_config = require_adapter_capability(account, "supports_user_info", "用户信息查询")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, user_info = refresh_account_user_cache(
        db,
        account,
        platform_config=platform_config,
    )

    if not success:
        raise HTTPException(status_code=400, detail=user_info.get("message", "获取信息失败"))

    quota = user_info.get("quota", 0)
    used_quota = user_info.get("used_quota", 0)
    request_count = user_info.get("request_count", 0)
    aff_history_quota = user_info.get("aff_history_quota", 0)

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

    require_adapter_capability(account, "supports_user_info", "用户信息查询")

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
    platform_config = require_adapter_capability(account, "supports_tokens", "Token 管理")
    if not account.anrouter_user_id:
        return 0

    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.get_tokens(
            session_cookie,
            user_id,
            current_platform["base_url"],
            token_api=current_platform["token_api"],
            console_url=current_platform["console_url"],
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
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

    require_adapter_capability(account, "supports_tokens", "Token 管理")
    if not account.anrouter_user_id:
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
    previous_status = account.health_status or "unknown"

    def emit_health_change() -> None:
        if previous_status == account.health_status:
            return
        publish_event(
            "health_changed",
            {
                "account_id": account.id,
                "username": account.username or "",
                "health_status": account.health_status,
                "health_message": account.health_message,
                "previous_status": previous_status,
            }
        )

    try:
        ensure_account_platform(account)
        platform_config = get_account_platform_config(account)
        adapter = get_platform_adapter(platform_config)
    except (HTTPException, ValueError) as exc:
        detail = exc.detail if isinstance(exc, HTTPException) else str(exc)
        account.health_status = "unhealthy"
        account.health_message = detail
        account.last_health_check = now
        db.commit()
        emit_health_change()
        return HealthCheckResponse(
            account_id=account.id, health_status="unhealthy",
            health_message=detail, checked_at=now,
        )

    if not adapter.capabilities.supports_health_check:
        account.health_status = "unknown"
        account.health_message = "当前平台未配置独立健康检查，请以最近签到结果为准"
        account.last_health_check = now
        db.commit()
        emit_health_change()
        return HealthCheckResponse(
            account_id=account.id, health_status="unknown",
            health_message=account.health_message, checked_at=now,
        )

    if adapter.capabilities.requires_external_user_id and not account.anrouter_user_id:
        account.health_status = "unhealthy"
        account.health_message = "缺少 user_id"
        account.last_health_check = now
        db.commit()
        emit_health_change()
        return HealthCheckResponse(
            account_id=account.id, health_status="unhealthy",
            health_message=account.health_message, checked_at=now,
        )


    # 尝试获取用户信息来验证凭证
    success, user_info = refresh_account_user_cache(
        db,
        account,
        platform_config=platform_config,
    )

    if success:
        account.health_status = "healthy"
        account.health_message = None
    else:
        account.health_status = "unhealthy"
        account.health_message = user_info.get("message", "凭证验证失败")

    account.last_health_check = now
    db.commit()
    emit_health_change()

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
    unknown_count = 0

    for account in accounts:
        result = check_account_health(db, account)
        results.append(result.model_dump())
        if result.health_status == "healthy":
            healthy_count += 1
        elif result.health_status == "unhealthy":
            unhealthy_count += 1
        else:
            unknown_count += 1

    return ApiResponse(
        success=True,
        message=f"健康检查完成: {healthy_count} 个健康, {unhealthy_count} 个异常, {unknown_count} 个未检查",
        data={
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "unknown_count": unknown_count,
            "results": results
        }
    )


@router.post("/{account_id}/tokens", response_model=ApiResponse)
def create_account_token(account_id: int, data: CreateTokenRequest, db: Session = Depends(get_db)):
    """创建 API Token"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    platform_config = require_adapter_capability(account, "supports_tokens", "Token 管理")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.create_token(
            session_cookie=session_cookie,
            user_id=user_id,
            base_url=current_platform["base_url"],
            name=data.name,
            remain_quota=data.remain_quota,
            expired_time=data.expired_time,
            unlimited_quota=data.unlimited_quota,
            model_limits_enabled=data.model_limits_enabled,
            model_limits=data.model_limits,
            allow_ips=data.allow_ips,
            group=data.group,
            token_api=current_platform["token_api"],
            console_url=current_platform["console_url"],
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
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

    platform_config = require_adapter_capability(account, "supports_models", "模型列表查询")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.get_models(
            session_cookie,
            user_id,
            current_platform["base_url"],
            models_api=current_platform["models_api"],
            console_url=current_platform["console_url"],
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
    )

    if not success:
        raise HTTPException(status_code=400, detail=result.get("message", "获取模型列表失败"))

    return ApiResponse(
        success=True,
        data=result.get("models", [])
    )


@router.get("/{account_id}/groups", response_model=ApiResponse)
def get_account_groups(account_id: int, db: Session = Depends(get_db)):
    """获取账号可用的分组列表（平台分组）"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    platform_config = require_adapter_capability(account, "supports_groups", "平台分组查询")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.get_groups(
            session_cookie,
            user_id,
            current_platform["base_url"],
            groups_api=current_platform["groups_api"],
            console_url=current_platform["console_url"],
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
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

    platform_config = require_adapter_capability(account, "supports_tokens", "Token 管理")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    # 尝试远程删除
    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.delete_token(
            session_cookie=session_cookie,
            user_id=user_id,
            base_url=current_platform["base_url"],
            token_api=current_platform["token_api"],
            console_url=current_platform["console_url"],
            token_id=token_id,
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
    )

    # 无论远程删除是否成功，都删除本地记录并同步
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
        return ApiResponse(success=True, message="本地已删除（远程可能已不存在）")


@router.put("/{account_id}/tokens/{token_id}", response_model=ApiResponse)
def update_account_token(account_id: int, token_id: int, data: dict, db: Session = Depends(get_db)):
    """更新 API Token"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    platform_config = require_adapter_capability(account, "supports_tokens", "Token 管理")
    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    # 确保 token_data 包含必要字段
    data["id"] = token_id
    data["user_id"] = account.anrouter_user_id

    success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.update_token(
            session_cookie=session_cookie,
            user_id=user_id,
            base_url=current_platform["base_url"],
            token_api=current_platform["token_api"],
            console_url=current_platform["console_url"],
            token_data=data,
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
    )

    if not success:
        sync_account_tokens(db, account)
        token_exists = db.query(ApiToken).filter(
            ApiToken.account_id == account_id,
            ApiToken.token_id == token_id
        ).first()

        if not token_exists:
            raise HTTPException(
                status_code=400,
                detail="更新失败：该令牌在远程已不存在，本地已同步清理"
            )
        else:
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

