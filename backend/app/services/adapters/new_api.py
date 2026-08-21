"""现有 AnyRouter/New API 协议适配器。"""
from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.account_cache import refresh_account_user_cache
from app.services.account_session import execute_with_session_refresh, login_account_session
from app.services.adapters.base import AdapterCapabilities
from app.services.anrouter import anrouter_service
from app.utils.platform import ADAPTER_TYPE_NEW_API, SIGN_MODE_LOGIN

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


class NewApiAdapter:
    adapter_type = ADAPTER_TYPE_NEW_API
    capabilities = AdapterCapabilities(
        requires_external_user_id=True,
        supports_user_info=True,
        supports_tokens=True,
        supports_models=True,
        supports_groups=True,
        supports_health_check=True,
    )

    def sign(
        self,
        db: Session,
        account: Account,
        platform_config: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        if platform_config.get("sign_mode") == SIGN_MODE_LOGIN:
            return self._login_sign(db, account, platform_config)

        if not account.anrouter_user_id:
            return False, {
                "success": False,
                "message": "账号缺少 user_id",
                "reward_quota": 0,
                "reward_unit": "quota",
                "already_signed": False,
            }

        request_success, result = execute_with_session_refresh(
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
        result.setdefault("reward_unit", "quota")
        return request_success, result

    def _login_sign(
        self,
        db: Session,
        account: Account,
        platform_config: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """通过登录触发签到，但不再把未知状态误报为“已签到”。"""
        before_quota = _safe_int(account.cached_quota)
        login_success, login_result = login_account_session(db, account, platform_config)
        if not login_success:
            return False, {
                "success": False,
                "message": login_result.get("message", "登录签到失败"),
                "reward_quota": 0,
                "reward_unit": "quota",
                "already_signed": False,
            }

        checked_in = login_result.get("checked_in")
        if checked_in is False:
            return True, {
                "success": False,
                "message": "登录成功，但平台返回未完成签到",
                "reward_quota": 0,
                "reward_unit": "quota",
                "already_signed": False,
                "raw": login_result.get("raw"),
            }

        reward_delta = 0
        cache_success, cache_result = refresh_account_user_cache(
            db,
            account,
            platform_config=platform_config,
        )
        if cache_success:
            reward_delta = _quota_delta(before_quota, account.cached_quota)
        else:
            logger.warning(
                "登录签到后刷新账号缓存失败，不影响登录签到结果: account_id=%s, message=%s",
                account.id,
                cache_result.get("message", "未知错误"),
            )

        message = (
            "登录成功，已完成签到"
            if checked_in is True
            else "登录成功，已触发签到（平台未返回签到状态）"
        )
        return True, {
            "success": True,
            "message": message,
            "reward_quota": reward_delta,
            "reward_unit": "quota",
            "already_signed": False,
            "raw": login_result.get("raw"),
        }

    def refresh_cache_after_sign(
        self,
        db: Session,
        account: Account,
        platform_config: Dict[str, Any],
        request_success: bool,
    ) -> None:
        if not request_success or platform_config.get("sign_mode") == SIGN_MODE_LOGIN:
            return

        cache_success, cache_result = refresh_account_user_cache(
            db,
            account,
            platform_config=platform_config,
        )
        if not cache_success:
            logger.warning(
                "签到后刷新账号缓存失败: account_id=%s, message=%s",
                account.id,
                cache_result.get("message", "未知错误"),
            )
