"""
账号会话与登录凭证服务
"""
import json
import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.anrouter import anrouter_service
from app.services.newapi_credentials import (
    DashboardCredential,
    ROTATE_KEY_ACCESS_EXPIRES_AT,
    ROTATE_KEY_ACCESS_TOKEN,
    ROTATE_KEY_REFRESH_TOKEN,
    SCHEME_LEGACY_COOKIE,
    SCHEME_PAT,
    SCHEME_REFRESH,
    build_credential,
)
from app.utils.platform import get_account_platform_config
from app.utils.proxy import DEFAULT_ACCOUNT_PROXY_MODE

logger = logging.getLogger(__name__)

# executor 第一个参数历史上是 session cookie 字符串，现在统一传凭证对象。
# 保留宽松签名，避免破坏既有的 12 处 lambda 调用点。
AccountExecutor = Callable[[Any, str, Dict[str, str]], Tuple[bool, Dict[str, Any]]]

AUTH_FAILURE_KEYWORDS = (
    "login",
    "please login",
    "unauthorized",
    "forbidden",
    "authentication",
    "auth",
    "session",
    "cookie",
    "expired",
    "登录",
    "未登录",
    "请先登录",
    "重新登录",
    "会话",
    "凭证",
    "过期",
    "失效",
)


def normalize_optional_str(value: Optional[str]) -> Optional[str]:
    """清洗可选字符串。"""
    if value is None:
        return None

    normalized = value.strip()
    return normalized or None


def normalize_optional_secret(value: Optional[str]) -> Optional[str]:
    """清理敏感字段，保留原始空白字符。"""
    if value is None:
        return None

    return value if value != "" else None


def has_login_credentials_values(login_username: Optional[str], login_password: Optional[str]) -> bool:
    """判断是否配置了完整的登录凭证。"""
    return bool(normalize_optional_str(login_username) and normalize_optional_secret(login_password))


def has_login_credentials(account: Account) -> bool:
    """判断账号是否支持自动登录刷新。"""
    return has_login_credentials_values(account.login_username, account.login_password)


def load_auth_data(account: Account) -> Dict[str, Any]:
    """读取账号 ``auth_data`` JSON 文本；内容不合法时按空字典处理。"""
    raw = account.auth_data
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        logger.warning("账号 auth_data 不是合法 JSON，按空处理: account_id=%s", account.id)
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def dump_auth_data(data: Optional[Dict[str, Any]]) -> Optional[str]:
    """序列化 ``auth_data``；空字典写 NULL，与既有 API 层行为一致。"""
    cleaned = {key: value for key, value in (data or {}).items() if value not in (None, "")}
    if not cleaned:
        return None
    return json.dumps(cleaned, ensure_ascii=False, separators=(",", ":"))


def build_account_credential(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> DashboardCredential:
    """按账号上存的认证方式构造面板凭证。

    ``new_api_refresh`` 方案会注入两个回调：``refresher`` 复用 ``anrouter_service`` 的
    代理与反爬管道；``on_rotate`` 把轮换后的令牌立刻写回 ``auth_data``。
    **轮换值不落盘就等于下次请求掉线**，所以这里必须 commit。
    """
    if platform_config is None:
        platform_config = get_account_platform_config(account)
    base_url = platform_config["base_url"]

    def refresher(refresh_token: str) -> Dict[str, Any]:
        return anrouter_service.refresh_dashboard_token(
            base_url,
            refresh_token,
            proxy_mode=account.proxy_mode or DEFAULT_ACCOUNT_PROXY_MODE,
            proxy_url=account.proxy_url,
        )

    def on_rotate(payload: Dict[str, Any]) -> None:
        current = load_auth_data(account)
        current.update(payload)
        account.auth_data = dump_auth_data(current)
        account.updated_at = datetime.now()
        db.commit()

    user_id = account.anrouter_user_id
    return build_credential(
        account.auth_type,
        load_auth_data(account),
        account.session_cookie,
        user_id=str(user_id) if user_id else None,
        refresher=refresher,
        on_rotate=on_rotate,
    )


def build_transient_credential(
    base_url: str,
    auth_type: Optional[str],
    auth_data: Optional[Dict[str, Any]],
    session_cookie: Optional[str],
    user_id: Optional[str] = None,
    *,
    proxy_mode: str = DEFAULT_ACCOUNT_PROXY_MODE,
    proxy_url: Optional[str] = None,
    on_rotate: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> DashboardCredential:
    """构造一个不绑定数据库行的凭证，用于账号落库前的凭证校验。

    校验 refresh 方案时服务端会**当场轮换** refresh token，所以调用方必须传
    ``on_rotate`` 把轮换后的新值收下来落库 —— 否则库里存的会是已经失效的旧值。
    """

    def refresher(refresh_token: str) -> Dict[str, Any]:
        return anrouter_service.refresh_dashboard_token(
            base_url,
            refresh_token,
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )

    return build_credential(
        auth_type,
        auth_data,
        session_cookie,
        user_id=user_id,
        refresher=refresher,
        on_rotate=on_rotate,
    )


def has_dashboard_credential(account: Account) -> bool:
    """判断账号是否已有任一可直接使用的面板凭证（不含账号密码）。"""
    auth_type = (account.auth_type or "").strip().lower()
    auth_data = load_auth_data(account)
    if auth_type == SCHEME_REFRESH:
        return bool(str(auth_data.get(ROTATE_KEY_REFRESH_TOKEN) or "").strip())
    if auth_type == SCHEME_PAT:
        return bool(str(auth_data.get("token") or "").strip())
    return bool(normalize_optional_str(account.session_cookie))


def is_auth_failure_message(message: Optional[str]) -> bool:
    """粗略判断错误是否由登录态失效引起。"""
    normalized = (message or "").strip().lower()
    if not normalized:
        return False

    if normalized == "响应解析失败":
        return True

    return any(keyword in normalized for keyword in AUTH_FAILURE_KEYWORDS)


def resolve_session_cookie(
    base_url: str,
    session_cookie: Optional[str],
    login_username: Optional[str],
    login_password: Optional[str],
    prefer_login: bool = False,
    proxy_mode: str = DEFAULT_ACCOUNT_PROXY_MODE,
    proxy_url: Optional[str] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """优先使用现有 session，或通过账号密码登录换取新的 session。"""
    cleaned_session = normalize_optional_str(session_cookie)
    cleaned_login_username = normalize_optional_str(login_username)
    cleaned_login_password = normalize_optional_secret(login_password)

    if prefer_login and has_login_credentials_values(cleaned_login_username, cleaned_login_password):
        return anrouter_service.login(
            base_url=base_url,
            username=cleaned_login_username or "",
            password=cleaned_login_password or "",
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )

    if cleaned_session:
        return True, {"session_cookie": cleaned_session}

    if has_login_credentials_values(cleaned_login_username, cleaned_login_password):
        return anrouter_service.login(
            base_url=base_url,
            username=cleaned_login_username or "",
            password=cleaned_login_password or "",
            proxy_mode=proxy_mode,
            proxy_url=proxy_url,
        )

    return False, {"message": "请填写 Session Cookie，或配置登录账号和密码"}


def persist_login_result(
    db: Session,
    account: Account,
    result: Dict[str, Any],
    *,
    strict_user_id: bool = False,
) -> Tuple[bool, Dict[str, Any]]:
    """把登录结果写回账号，自动区分新旧两套鉴权方案。

    新版 new-api 登录响应带 ``access_token`` + ``new_api_refresh`` cookie，此时写
    ``auth_type`` / ``auth_data``；旧版只有 ``session`` cookie，行为与改造前一致。

    :param strict_user_id: True 时 user_id 非法直接失败（登录签到要求准确身份），
        False 时忽略（自动刷新场景不因此中断）
    """
    scheme = (result.get("auth_scheme") or SCHEME_LEGACY_COOKIE).strip().lower()

    if scheme == SCHEME_REFRESH:
        refresh_token = normalize_optional_secret(result.get(ROTATE_KEY_REFRESH_TOKEN))
        if not refresh_token:
            return False, {"message": "登录成功，但未获取到 refresh token"}
        auth_data = load_auth_data(account)
        auth_data.update(
            {
                ROTATE_KEY_REFRESH_TOKEN: refresh_token,
                ROTATE_KEY_ACCESS_TOKEN: result.get(ROTATE_KEY_ACCESS_TOKEN) or "",
                ROTATE_KEY_ACCESS_EXPIRES_AT: int(result.get(ROTATE_KEY_ACCESS_EXPIRES_AT) or 0),
            }
        )
        # PAT 与 refresh 互斥：切到 refresh 方案时清掉可能残留的 PAT
        auth_data.pop("token", None)
        account.auth_type = SCHEME_REFRESH
        account.auth_data = dump_auth_data(auth_data)
        # 新方案没有 session cookie，留着只会误导排查
        account.session_cookie = None
    else:
        new_session_cookie = normalize_optional_str(result.get("session_cookie"))
        if not new_session_cookie:
            return False, {"message": "登录成功，但未获取到新的 Session Cookie"}
        account.session_cookie = new_session_cookie

    user_id = normalize_optional_str(result.get("user_id"))
    if user_id:
        try:
            account.anrouter_user_id = int(user_id)
        except (TypeError, ValueError):
            if strict_user_id:
                return False, {"message": "登录成功但 User ID 无效，请手动检查账号"}
    if result.get("username"):
        account.username = result.get("username")
    if result.get("display_name"):
        account.display_name = result.get("display_name")
    account.updated_at = datetime.now()
    db.commit()
    db.refresh(account)

    return True, {"auth_scheme": scheme, "user_id": user_id}


def refresh_account_session(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """使用账号密码重新登录并刷新数据库中的凭证。"""
    if not has_login_credentials(account):
        return False, {"message": "账号未配置登录账号和密码，无法自动刷新 Session"}

    if platform_config is None:
        platform_config = get_account_platform_config(account)

    success, result = resolve_session_cookie(
        base_url=platform_config["base_url"],
        session_cookie=None,
        login_username=account.login_username,
        login_password=account.login_password,
        prefer_login=True,
        proxy_mode=account.proxy_mode or DEFAULT_ACCOUNT_PROXY_MODE,
        proxy_url=account.proxy_url,
    )
    if not success:
        return False, result

    persisted, persist_result = persist_login_result(db, account, result)
    if not persisted:
        return False, persist_result

    return True, {
        "auth_scheme": persist_result.get("auth_scheme"),
        "session_cookie": account.session_cookie,
        "user_id": persist_result.get("user_id"),
        "message": "登录凭证已自动刷新",
    }


def login_account_session(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """强制使用账号密码登录，并同步账号凭证/user_id 基础信息。"""
    if not has_login_credentials(account):
        return False, {"message": "该平台需要通过登录签到，请先为账号配置登录账号和密码"}

    if platform_config is None:
        platform_config = get_account_platform_config(account)

    success, result = resolve_session_cookie(
        base_url=platform_config["base_url"],
        session_cookie=None,
        login_username=account.login_username,
        login_password=account.login_password,
        prefer_login=True,
        proxy_mode=account.proxy_mode or DEFAULT_ACCOUNT_PROXY_MODE,
        proxy_url=account.proxy_url,
    )
    if not success:
        return False, result

    persisted, persist_result = persist_login_result(db, account, result, strict_user_id=True)
    if not persisted:
        return False, persist_result

    return True, result


def execute_with_session_refresh(
    db: Session,
    account: Account,
    executor: AccountExecutor,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """执行平台请求；鉴权失效时先让凭证自愈，仍不行才用账号密码重登并重试一次。

    自愈优先于重登：新版 new-api 的 access token 只有 15 分钟寿命，刷 JWT 是常态操作，
    而重新登录会新建会话，服务端对会话数和签发频率都有上限。
    """
    if platform_config is None:
        platform_config = get_account_platform_config(account)

    # 完全没有可用凭证但配了账号密码 → 先登录换一份
    if not has_dashboard_credential(account) and has_login_credentials(account):
        refreshed, refresh_result = refresh_account_session(db, account, platform_config)
        if not refreshed:
            return False, {
                "message": refresh_result.get("message", "自动登录失败，无法获取登录凭证"),
            }

    credential = build_account_credential(db, account, platform_config)
    user_id = str(account.anrouter_user_id)

    request_success, result = executor(credential, user_id, platform_config)

    message = result.get("message") if isinstance(result, dict) else None
    result_success = result.get("success") if isinstance(result, dict) else None
    auth_failed = (
        not credential.is_usable
        or (request_success and result_success is False and is_auth_failure_message(message))
        or (not request_success and is_auth_failure_message(message))
    )

    if not auth_failed:
        return request_success, result

    # 1) 凭证自愈：refresh 方案在这里换新 JWT 并把轮换值落盘
    if not credential.needs_relogin and credential.handle_unauthorized():
        return executor(credential, user_id, platform_config)

    # 2) 自愈无门 → 回落账号密码重登
    if not has_login_credentials(account):
        return request_success, result

    refreshed, refresh_result = refresh_account_session(db, account, platform_config)
    if not refreshed:
        return False, {
            "message": refresh_result.get("message") or message or "自动登录失败",
        }

    return executor(
        build_account_credential(db, account, platform_config),
        str(account.anrouter_user_id),
        platform_config,
    )
