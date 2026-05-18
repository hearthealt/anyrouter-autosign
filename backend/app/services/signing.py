"""
平台签到执行服务
"""
import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.account_cache import refresh_account_user_cache
from app.services.account_session import execute_with_session_refresh, login_account_session
from app.services.anrouter import anrouter_service
from app.utils.platform import SIGN_MODE_LOGIN, get_account_platform_config

logger = logging.getLogger(__name__)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _quota_delta(before_quota: int, after_quota: int) -> int:
    return max(0, _safe_int(after_quota) - _safe_int(before_quota))


def execute_sign_request(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """按平台签到模式执行一次签到。"""
    if platform_config is None:
        platform_config = get_account_platform_config(account)

    if platform_config.get("sign_mode") == SIGN_MODE_LOGIN:
        return execute_login_sign_request(db, account, platform_config)

    if not account.anrouter_user_id:
        return False, {
            "success": False,
            "message": "账号缺少 user_id",
            "reward_quota": 0,
            "already_signed": False,
        }

    return execute_api_sign_request(db, account, platform_config)


def execute_api_sign_request(
    db: Session,
    account: Account,
    platform_config: Dict[str, str],
) -> Tuple[bool, Dict[str, Any]]:
    """调用平台签到接口。"""
    return execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.sign_in(
            session_cookie,
            user_id,
            current_platform["base_url"],
            sign_api=current_platform["sign_api"],
            checkin_api=current_platform["checkin_api"],
            console_url=current_platform["console_url"],
            captcha_api=current_platform.get("captcha_api", ""),
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
        platform_config=platform_config,
    )


def execute_login_sign_request(
    db: Session,
    account: Account,
    platform_config: Dict[str, str],
) -> Tuple[bool, Dict[str, Any]]:
    """通过强制登录触发平台签到。"""
    before_quota = _safe_int(account.cached_quota)

    login_success, login_result = login_account_session(db, account, platform_config)
    if not login_success:
        return False, {
            "success": False,
            "message": login_result.get("message", "登录签到失败"),
            "reward_quota": 0,
            "already_signed": False,
        }

    login_checked_in = login_result.get("checked_in") is True

    cache_success, cache_result = refresh_account_user_cache(
        db,
        account,
        platform_config=platform_config,
    )
    if not cache_success:
        logger.warning(
            "登录签到后刷新账号缓存失败: account_id=%s, message=%s",
            account.id,
            cache_result.get("message", "未知错误"),
        )
        return False, {
            "success": False,
            "message": cache_result.get("message", "登录成功，但刷新余额失败，无法判断签到结果"),
            "reward_quota": 0,
            "already_signed": False,
        }

    reward_delta = _quota_delta(before_quota, account.cached_quota)
    if login_checked_in:
        return True, {
            "success": True,
            "message": "登录成功，已完成签到",
            "reward_quota": reward_delta,
            "already_signed": False,
            "raw": login_result.get("raw"),
        }

    return True, {
        "success": True,
        "message": "今日已签到",
        "reward_quota": 0,
        "already_signed": True,
        "raw": login_result.get("raw"),
    }


def refresh_account_cache_after_sign(
    db: Session,
    account: Account,
    platform_config: Dict[str, str],
    request_success: bool,
) -> None:
    """签到请求成功返回后同步账号缓存。"""
    if not request_success:
        return

    if platform_config.get("sign_mode") == SIGN_MODE_LOGIN:
        return

    cache_success, cache_result = refresh_account_user_cache(
        db,
        account,
        platform_config=platform_config,
    )
    if cache_success:
        return

    logger.warning(
        "签到后刷新账号缓存失败: account_id=%s, message=%s",
        account.id,
        cache_result.get("message", "未知错误"),
    )
