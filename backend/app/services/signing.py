"""平台签到执行服务。"""
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Account
from app.services.adapters import adapter_registry
from app.utils.platform import get_account_platform_config


def execute_sign_request(
    db: Session,
    account: Account,
    platform_config: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Dict[str, Any]]:
    """按平台 adapter_type 分发签到请求。"""
    if platform_config is None:
        platform_config = get_account_platform_config(account)

    adapter = adapter_registry.get(platform_config["adapter_type"])
    return adapter.sign(db, account, platform_config)


def refresh_account_cache_after_sign(
    db: Session,
    account: Account,
    platform_config: Dict[str, Any],
    request_success: bool,
) -> None:
    """由适配器自行决定是否需要同步用户缓存。"""
    adapter = adapter_registry.get(platform_config["adapter_type"])
    refresh_hook = getattr(adapter, "refresh_cache_after_sign", None)
    if callable(refresh_hook):
        refresh_hook(db, account, platform_config, request_success)
