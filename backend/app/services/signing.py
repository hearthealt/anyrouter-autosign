"""平台签到执行服务。"""
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterable, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import SessionLocal
from app.models import Account
from app.services.adapters import adapter_registry
from app.utils.platform import get_account_platform_config

logger = logging.getLogger(__name__)


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


def _skipped_sign_result(account_id: int, username: str, message: str) -> Dict[str, Any]:
    """构造无需执行签到的结果。"""
    return {
        "account_id": account_id,
        "username": username,
        "skipped": True,
        "success": False,
        "already_signed": False,
        "message": message,
        "reward_quota": 0,
        "reward_display": None,
        "reward_unit": "quota",
    }


def execute_account_sign(account_id: int) -> Dict[str, Any]:
    """使用独立数据库会话执行单账号签到，供线程池安全调用。"""
    db = SessionLocal()
    account: Optional[Account] = None
    username = f"账号 {account_id}"
    reward_unit = "quota"

    try:
        account = (
            db.query(Account)
            .options(joinedload(Account.platform))
            .filter(Account.id == account_id)
            .first()
        )
        if not account:
            return _skipped_sign_result(account_id, username, "账号不存在")

        username = account.username or username
        if not account.is_active:
            return _skipped_sign_result(account_id, username, "账号已禁用")
        if not account.platform_id or not account.platform:
            return _skipped_sign_result(account_id, username, "账号未配置平台")

        platform_config = get_account_platform_config(account)
        reward_unit = "quota" if platform_config.get("adapter_type") == "new_api" else "count"
        request_success, result = execute_sign_request(
            db,
            account,
            platform_config=platform_config,
        )
        try:
            refresh_account_cache_after_sign(
                db,
                account,
                platform_config=platform_config,
                request_success=request_success,
            )
        except Exception as exc:
            # 缓存同步失败不应覆盖已经拿到的签到结果；回滚缓存写入后再返回签到状态。
            db.rollback()
            logger.warning(
                "账号 %s 签到后刷新缓存异常，不影响签到结果: %s",
                account_id,
                exc,
            )
        else:
            db.commit()

        if not request_success:
            return {
                "account_id": account.id,
                "username": account.username or username,
                "skipped": False,
                "success": False,
                "already_signed": False,
                "message": result.get("message", "签到失败"),
                "reward_quota": 0,
                "reward_display": result.get("reward_display"),
                "reward_unit": result.get("reward_unit") or reward_unit,
            }

        return {
            "account_id": account.id,
            "username": account.username or username,
            "skipped": False,
            "success": bool(result.get("success", False)),
            "already_signed": bool(result.get("already_signed", False)),
            "message": result.get("message", ""),
            "reward_quota": result.get("reward_quota", 0),
            "reward_display": result.get("reward_display"),
            "reward_unit": result.get("reward_unit") or reward_unit,
        }
    except Exception as exc:
        db.rollback()
        logger.exception("账号 %s 并发签到异常: %s", account_id, exc)
        return {
            "account_id": account_id,
            "username": username,
            "skipped": False,
            "success": False,
            "already_signed": False,
            "message": str(exc) or "签到异常",
            "reward_quota": 0,
            "reward_display": None,
            "reward_unit": reward_unit,
        }
    finally:
        db.close()


def execute_sign_batch(
    account_ids: Iterable[int],
    max_workers: Optional[int] = None,
) -> list[Dict[str, Any]]:
    """受限并发执行多个账号签到，结果顺序与账号 ID 输入顺序一致。"""
    normalized_ids = [int(account_id) for account_id in account_ids]
    if not normalized_ids:
        return []

    configured_workers = max_workers if max_workers is not None else settings.sign_concurrency
    try:
        worker_count = int(configured_workers)
    except (TypeError, ValueError):
        worker_count = 8
    worker_count = max(1, min(worker_count, len(normalized_ids), 32))

    logger.info("开始并发签到: 账号 %s 个，并发数 %s", len(normalized_ids), worker_count)
    with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="account-sign") as executor:
        return list(executor.map(execute_account_sign, normalized_ids))
