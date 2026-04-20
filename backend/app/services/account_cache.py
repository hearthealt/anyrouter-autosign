"""
账号缓存同步服务
"""
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.account_session import execute_with_session_refresh
from app.services.anrouter import anrouter_service
from app.utils.platform import get_account_platform_config


def apply_account_user_info(account: Account, user_info: Dict[str, Any], now: Optional[datetime] = None) -> None:
    """把远端用户信息回写到账号缓存。"""
    current_time = now or datetime.now()

    account.cached_quota = user_info.get("quota", 0)
    account.cached_used_quota = user_info.get("used_quota", 0)
    account.cached_request_count = user_info.get("request_count", 0)
    account.cached_user_group = user_info.get("group", "default")
    account.cached_aff_code = user_info.get("aff_code")
    account.cached_aff_count = user_info.get("aff_count", 0)
    account.cached_aff_history_quota = user_info.get("aff_history_quota", 0)
    account.quota_updated_at = current_time

    if user_info.get("username"):
        account.username = user_info.get("username")
    if user_info.get("display_name"):
        account.display_name = user_info.get("display_name")


def refresh_account_user_cache(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, str]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """从远端拉取最新用户信息并更新账号缓存。"""
    if platform_config is None:
        platform_config = get_account_platform_config(account)

    success, user_info = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.get_user_info(
            session_cookie,
            user_id,
            current_platform["base_url"],
            user_api=current_platform["user_api"],
            console_url=current_platform["console_url"]
        ),
        platform_config=platform_config,
    )

    if not success:
        return False, user_info

    apply_account_user_info(account, user_info)
    return True, user_info
