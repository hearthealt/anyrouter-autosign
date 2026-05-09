"""
账号会话与登录凭证服务
"""
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.anrouter import anrouter_service
from app.utils.platform import get_account_platform_config
from app.utils.proxy import DEFAULT_ACCOUNT_PROXY_MODE


AccountExecutor = Callable[[str, str, Dict[str, str]], Tuple[bool, Dict[str, Any]]]

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


def refresh_account_session(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """使用账号密码重新登录并刷新数据库中的 session。"""
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

    new_session_cookie = normalize_optional_str(result.get("session_cookie"))
    if not new_session_cookie:
        return False, {"message": "登录成功，但未获取到新的 Session Cookie"}

    account.session_cookie = new_session_cookie
    refreshed_user_id = normalize_optional_str(result.get("user_id"))
    if refreshed_user_id:
        try:
            account.anrouter_user_id = int(refreshed_user_id)
        except (TypeError, ValueError):
            pass
    if result.get("username"):
        account.username = result.get("username")
    if result.get("display_name"):
        account.display_name = result.get("display_name")
    account.updated_at = datetime.now()
    db.commit()
    db.refresh(account)

    return True, {
        "session_cookie": new_session_cookie,
        "user_id": refreshed_user_id,
        "message": "Session 已自动刷新",
    }


def login_account_session(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """强制使用账号密码登录，并同步账号 session/user_id 基础信息。"""
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

    new_session_cookie = normalize_optional_str(result.get("session_cookie"))
    if not new_session_cookie:
        return False, {"message": "登录成功，但未获取到新的 Session Cookie"}

    account.session_cookie = new_session_cookie
    user_id = normalize_optional_str(result.get("user_id"))
    if user_id:
        try:
            account.anrouter_user_id = int(user_id)
        except (TypeError, ValueError):
            return False, {"message": "登录成功但 User ID 无效，请手动检查账号"}
    if result.get("username"):
        account.username = result.get("username")
    if result.get("display_name"):
        account.display_name = result.get("display_name")
    account.updated_at = datetime.now()
    db.commit()
    db.refresh(account)

    return True, result


def execute_with_session_refresh(
    db: Session,
    account: Account,
    executor: AccountExecutor,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """执行平台请求，若登录态失效则自动刷新 session 后重试一次。"""
    if platform_config is None:
        platform_config = get_account_platform_config(account)

    if not normalize_optional_str(account.session_cookie) and has_login_credentials(account):
        refreshed, refresh_result = refresh_account_session(db, account, platform_config)
        if not refreshed:
            return False, {
                "message": refresh_result.get("message", "自动登录失败，无法获取 Session"),
            }

    request_success, result = executor(
        account.session_cookie or "",
        str(account.anrouter_user_id),
        platform_config,
    )

    if not has_login_credentials(account):
        return request_success, result

    message = result.get("message") if isinstance(result, dict) else None
    result_success = result.get("success") if isinstance(result, dict) else None
    should_refresh = (
        not normalize_optional_str(account.session_cookie)
        or (request_success and result_success is False and is_auth_failure_message(message))
        or (not request_success and is_auth_failure_message(message))
    )

    if not should_refresh:
        return request_success, result

    refreshed, refresh_result = refresh_account_session(db, account, platform_config)
    if not refreshed:
        return False, {
            "message": refresh_result.get("message") or message or "自动登录失败",
        }

    return executor(
        account.session_cookie or "",
        str(account.anrouter_user_id),
        platform_config,
    )
