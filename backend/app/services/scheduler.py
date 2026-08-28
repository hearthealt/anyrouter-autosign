"""
定时任务调度器
"""
import json
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from app.database import SessionLocal
from app.models import Account, SignLog, Setting, NotifyChannel
from app.services import (
    anrouter_service,
    execute_sign_request,
    execute_with_session_refresh,
    refresh_account_cache_after_sign,
)
from app.services.signing import execute_sign_batch
from app.services.events import publish_event
from app.services.notify import NotifyFactory
from app.utils import add_reward_total, format_quota, format_reward_totals, get_account_platform_config

logger = logging.getLogger(__name__)

# 全局调度器实例
scheduler = BackgroundScheduler()


def get_setting_value(db, key: str, default=None):
    """获取设置值"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        try:
            return json.loads(setting.value)
        except:
            return setting.value
    return default


def normalize_channel_ids(channel_ids) -> list[int]:
    """清理推送渠道 ID 列表，避免脏配置影响定时任务。"""
    normalized = []
    seen = set()
    if not isinstance(channel_ids, list):
        return normalized
    for channel_id in channel_ids:
        try:
            normalized_id = int(channel_id)
        except (TypeError, ValueError):
            continue
        if normalized_id <= 0 or normalized_id in seen:
            continue
        seen.add(normalized_id)
        normalized.append(normalized_id)
    return normalized


def _global_channel_config(channel_type: str, config: dict) -> dict:
    """构造全局通知使用的渠道附加配置。"""
    if channel_type == "email":
        return {"to_email": config.get("to_email") or config.get("username")}
    return {}


def send_global_notification(db, title: str, content: str, channel_ids: list[int]):
    """向指定的全局推送渠道发送通知。"""
    if not channel_ids:
        logger.info("未选择签到推送渠道，跳过全局通知")
        return

    channels = db.query(NotifyChannel).filter(
        NotifyChannel.id.in_(channel_ids),
        NotifyChannel.is_enabled == True
    ).all()
    if not channels:
        logger.info("没有可用的签到推送渠道，跳过全局通知")
        return

    for channel in channels:
        try:
            config = json.loads(channel.config)
            notifier = NotifyFactory.create(channel.type, config)
            result = notifier.send(title, content, _global_channel_config(channel.type, config))
            if result:
                logger.info(f"全局通知发送成功: {channel.name}")
            else:
                logger.error(f"全局通知发送失败: {channel.name}")
        except Exception as e:
            logger.error(f"全局通知发送异常 {channel.name}: {e}")


def build_sign_summary_content(
    total_count: int,
    success_count: int,
    already_signed_count: int,
    fail_count: int,
    reward_quota: int,
    failed_items: list,
    reward_totals: dict[str, float] | None = None,
) -> str:
    """构造定时签到汇总通知，按单位展示不同平台的奖励。"""
    reward_summary = format_reward_totals(reward_totals) if reward_totals else format_quota(reward_quota)
    lines = [
        f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"本次签到账号: {total_count} 个",
        f"成功: {success_count} 个",
        f"已签到: {already_signed_count} 个",
        f"失败: {fail_count} 个",
        f"签到奖励: {reward_summary}",
    ]

    if failed_items:
        lines.append("")
        lines.append("失败账号:")
        for item in failed_items[:10]:
            lines.append(f"- {item['username']}: {item['message']}")
        if len(failed_items) > 10:
            lines.append(f"- 其余 {len(failed_items) - 10} 个失败账号请查看签到日志")

    return "\n".join(lines)


def send_sign_summary_notification(
    db,
    title: str,
    total_count: int,
    success_count: int,
    already_signed_count: int,
    fail_count: int,
    reward_quota: int,
    failed_items: list,
    reward_totals: dict[str, float] | None = None,
):
    """发送定时签到全局汇总。"""
    if total_count <= 0:
        return
    if not get_setting_value(db, "sign_notify_enabled", False):
        logger.info("签到推送未启用，跳过定时签到汇总通知")
        return
    channel_ids = normalize_channel_ids(get_setting_value(db, "sign_notify_channel_ids", []) or [])
    content = build_sign_summary_content(
        total_count,
        success_count,
        already_signed_count,
        fail_count,
        reward_quota,
        failed_items,
        reward_totals,
    )
    send_global_notification(db, title, content, channel_ids)


def execute_sign(db, account) -> dict:
    """执行单个账号签到并返回统一结果。"""
    platform_config = get_account_platform_config(account)
    request_success, result = execute_sign_request(
        db,
        account,
        platform_config=platform_config,
    )

    refresh_account_cache_after_sign(
        db,
        account,
        platform_config=platform_config,
        request_success=request_success,
    )

    if not request_success:
        return {
            "success": False,
            "already_signed": False,
            "message": result.get("message", "签到失败"),
            "reward_quota": 0,
            "reward_unit": "quota" if platform_config.get("adapter_type") == "new_api" else "count",
        }

    return {
        "success": bool(result.get("success", False)),
        "already_signed": bool(result.get("already_signed", False)),
        "message": result.get("message", ""),
        "reward_quota": result.get("reward_quota", 0),
        "reward_display": result.get("reward_display"),
        "reward_unit": result.get("reward_unit") or ("quota" if platform_config.get("adapter_type") == "new_api" else "count"),
    }


def build_sign_message(
    message: str,
    reward_quota: int,
    already_signed: bool = False,
    reward_display: str | None = None,
) -> str:
    """构造用于日志和通知的签到结果文案。"""
    if already_signed:
        return "今日已签到"
    if reward_quota > 0:
        base_message = message or "签到成功"
        return f"{base_message}，获得 {reward_display or format_quota(reward_quota)}"
    return message or "签到成功"


def auto_sign_job():
    """自动签到任务"""
    logger.info("开始执行自动签到任务...")
    db = SessionLocal()

    try:
        enabled = get_setting_value(db, "auto_sign_enabled", False)
        if not enabled:
            logger.info("自动签到未启用，跳过")
            return

        account_ids = [
            account_id
            for (account_id,) in db.query(Account.id).filter(
                Account.is_active == True,
                Account.platform_id.isnot(None)
            ).all()
        ]

        if not account_ids:
            logger.info("没有可签到的账号")
            return

        retry_enabled = get_setting_value(db, "sign_retry_enabled", True)
        max_retries = get_setting_value(db, "sign_max_retries", 3)
        retry_interval = get_setting_value(db, "sign_retry_interval", 30)

        success_count = 0
        fail_count = 0
        skip_count = 0
        total_reward_quota = 0
        reward_totals: dict[str, float] = {}
        failed_items = []
        retry_accounts = []
        event_payloads = []

        # 先结束设置和账号列表查询事务，再由线程池中的独立 Session 并发签到。
        db.commit()
        sign_results = execute_sign_batch(account_ids)

        for result in sign_results:
            if result.get("skipped"):
                logger.info(
                    "账号 %s 跳过签到: %s",
                    result.get("username") or result.get("account_id"),
                    result.get("message", "账号不可用"),
                )
                continue

            account_id = result["account_id"]
            username = result.get("username") or f"账号 {account_id}"
            sign_success = bool(result.get("success", False))
            already_signed = bool(result.get("already_signed", False))
            message = result.get("message", "")
            reward_quota = result.get("reward_quota", 0)
            reward_display = result.get("reward_display") or format_quota(reward_quota)
            reward_unit = result.get("reward_unit") or "quota"

            if already_signed:
                log_message = "今日已签到"
                log_status = "already_signed"
                skip_count += 1
            elif sign_success:
                log_message = build_sign_message(
                    message,
                    reward_quota,
                    reward_display=reward_display,
                )
                log_status = "success"
                success_count += 1
                add_reward_total(reward_totals, reward_quota, reward_unit)
                if reward_unit == "quota":
                    total_reward_quota += reward_quota
            else:
                log_message = message or "签到失败"
                log_status = "failed"
                fail_count += 1
                failed_items.append({
                    "username": username,
                    "message": log_message,
                })

            log = SignLog(
                account_id=account_id,
                success=sign_success,
                message=log_message,
                reward_quota=reward_quota,
                reward_display=reward_display,
                reward_unit=reward_unit,
                retry_count=0,
                status=log_status,
            )
            db.add(log)
            db.flush()

            logger.info("账号 %s 签到: %s", username, log_message)

            if retry_enabled and not sign_success and not already_signed:
                retry_accounts.append({
                    "account_id": account_id,
                    "retry_count": 0,
                    "log_id": log.id,
                })

            event_payloads.append({
                "account_id": account_id,
                "username": username,
                "success": sign_success,
                "already_signed": already_signed,
                "message": log_message,
                "reward_quota": reward_quota,
                "reward_display": reward_display,
                "reward_unit": reward_unit,
            })

        db.commit()
        for payload in event_payloads:
            publish_event("sign_completed", payload)
        logger.info(f"自动签到完成: 成功 {success_count}, 已签 {skip_count}, 失败 {fail_count}")
        send_sign_summary_notification(
            db,
            "定时签到汇总",
            len(event_payloads),
            success_count,
            skip_count,
            fail_count,
            total_reward_quota,
            failed_items,
            reward_totals,
        )

        if retry_accounts and retry_enabled:
            schedule_retry_sign(retry_accounts, max_retries, retry_interval)

    except Exception as e:
        logger.error(f"自动签到任务异常: {e}")
    finally:
        db.close()


def schedule_retry_sign(accounts: list, max_retries: int, retry_interval: int):
    """安排重试签到任务"""
    if not accounts:
        return

    retry_time = datetime.now() + timedelta(minutes=retry_interval)
    job_id = f"retry_sign_{retry_time.strftime('%Y%m%d%H%M%S')}"

    scheduler.add_job(
        retry_sign_job,
        DateTrigger(run_date=retry_time),
        id=job_id,
        replace_existing=True,
        args=[accounts, max_retries, retry_interval]
    )
    logger.info(f"已安排重试任务 {job_id}，将在 {retry_time.strftime('%H:%M:%S')} 执行")


def retry_sign_job(accounts: list, max_retries: int, retry_interval: int):
    """并发执行失败账号的重试签到任务。"""
    logger.info(f"开始执行重试签到任务，共 {len(accounts)} 个账号...")
    db = SessionLocal()

    try:
        success_count = 0
        fail_count = 0
        already_signed_count = 0
        total_reward_quota = 0
        reward_totals: dict[str, float] = {}
        failed_items = []
        retry_accounts = []
        event_payloads = []

        retry_items = [
            {
                "account_id": int(item["account_id"]),
                "retry_count": int(item.get("retry_count", 0)) + 1,
                "log_id": item.get("log_id"),
            }
            for item in accounts
        ]

        # 签到线程各自创建 Session；当前 Session 只负责更新原签到日志和通知统计。
        sign_results = execute_sign_batch(item["account_id"] for item in retry_items)

        for item, result in zip(retry_items, sign_results):
            account_id = item["account_id"]
            retry_count = item["retry_count"]
            log_id = item.get("log_id")

            if result.get("skipped"):
                logger.info(
                    "账号 %s 跳过重试签到: %s",
                    result.get("username") or account_id,
                    result.get("message", "账号不可用"),
                )
                continue

            username = result.get("username") or f"账号 {account_id}"
            sign_success = bool(result.get("success", False))
            already_signed = bool(result.get("already_signed", False))
            message = result.get("message", "")
            reward_quota = result.get("reward_quota", 0)
            reward_display = result.get("reward_display") or format_quota(reward_quota)
            reward_unit = result.get("reward_unit") or "quota"
            log = db.query(SignLog).filter(SignLog.id == log_id).first() if log_id else None

            if already_signed:
                log_message = f"重试{retry_count}次后: 今日已签到"
                log_status = "already_signed"
                already_signed_count += 1
            elif sign_success:
                log_message = (
                    f"重试{retry_count}次后: "
                    f"{build_sign_message(message, reward_quota, reward_display=reward_display)}"
                )
                log_status = "success"
                success_count += 1
                add_reward_total(reward_totals, reward_quota, reward_unit)
                if reward_unit == "quota":
                    total_reward_quota += reward_quota
            else:
                log_message = f"重试{retry_count}次后: {message or '签到失败'}"
                log_status = "failed"
                fail_count += 1
                failed_items.append({
                    "username": username,
                    "message": log_message,
                })
                if retry_count < max_retries:
                    retry_accounts.append({
                        "account_id": account_id,
                        "retry_count": retry_count,
                        "log_id": log_id,
                    })

            if log:
                log.sign_time = datetime.now()
                log.success = sign_success
                log.message = log_message
                log.reward_quota = reward_quota
                log.reward_display = reward_display
                log.reward_unit = reward_unit
                log.retry_count = retry_count
                log.status = log_status
            else:
                log = SignLog(
                    account_id=account_id,
                    success=sign_success,
                    message=log_message,
                    reward_quota=reward_quota,
                    reward_display=reward_display,
                    reward_unit=reward_unit,
                    retry_count=retry_count,
                    status=log_status,
                )
                db.add(log)
                db.flush()
                log_id = log.id
                if retry_accounts and retry_accounts[-1]["account_id"] == account_id:
                    retry_accounts[-1]["log_id"] = log_id

            logger.info("账号 %s 重试签到(第%s次): %s", username, retry_count, log_message)

            event_payloads.append({
                "account_id": account_id,
                "username": username,
                "success": sign_success,
                "already_signed": already_signed,
                "message": log_message,
                "reward_quota": reward_quota,
                "reward_display": reward_display,
                "reward_unit": reward_unit,
            })

        db.commit()
        for payload in event_payloads:
            publish_event("sign_completed", payload)
        logger.info(
            "重试签到完成: 成功 %s, 已签 %s, 失败 %s",
            success_count,
            already_signed_count,
            fail_count,
        )
        send_sign_summary_notification(
            db,
            "定时签到重试汇总",
            len(event_payloads),
            success_count,
            already_signed_count,
            fail_count,
            total_reward_quota,
            failed_items,
            reward_totals,
        )

        if retry_accounts:
            schedule_retry_sign(retry_accounts, max_retries, retry_interval)

    except Exception as e:
        db.rollback()
        logger.error(f"重试签到任务异常: {e}")
    finally:
        db.close()


def update_sign_schedule():
    """更新签到定时任务"""
    db = SessionLocal()

    try:
        enabled = get_setting_value(db, "auto_sign_enabled", False)
        sign_time = get_setting_value(db, "auto_sign_time", "08:00")

        if scheduler.get_job("auto_sign"):
            scheduler.remove_job("auto_sign")

        if enabled and sign_time:
            hour, minute = map(int, sign_time.split(":"))

            scheduler.add_job(
                auto_sign_job,
                CronTrigger(hour=hour, minute=minute),
                id="auto_sign",
                replace_existing=True
            )
            logger.info(f"自动签到任务已设置: 每天 {sign_time}")
        else:
            logger.info("自动签到任务已禁用")

    except Exception as e:
        logger.error(f"更新签到定时任务失败: {e}")
    finally:
        db.close()


def health_check_job():
    """账号健康检查任务"""
    logger.info("开始执行账号健康检查任务...")
    db = SessionLocal()

    try:
        enabled = get_setting_value(db, "health_check_enabled", True)
        if not enabled:
            logger.info("健康检查未启用，跳过")
            return

        accounts = db.query(Account).filter(
            Account.is_active == True,
            Account.anrouter_user_id.isnot(None),
            Account.platform_id.isnot(None)
        ).all()

        if not accounts:
            logger.info("没有需要检查的账号")
            return

        healthy_count = 0
        unhealthy_count = 0
        health_events = []

        for account in accounts:
            try:
                previous_status = account.health_status or "unknown"
                platform_config = get_account_platform_config(account)

                success, user_info = execute_with_session_refresh(
                    db,
                    account,
                    lambda session_cookie, user_id, current_platform: anrouter_service.get_user_info(
                        session_cookie,
                        user_id,
                        current_platform["base_url"],
                        user_api=current_platform["user_api"],
                        console_url=current_platform["console_url"],
                        proxy_mode=account.proxy_mode,
                        proxy_url=account.proxy_url,
                    ),
                    platform_config=platform_config,
                )

                now = datetime.now()
                if success:
                    account.health_status = "healthy"
                    account.health_message = None
                    if user_info.get("username"):
                        account.username = user_info.get("username")
                    if user_info.get("display_name"):
                        account.display_name = user_info.get("display_name")
                    account.cached_quota = user_info.get("quota", 0)
                    account.cached_used_quota = user_info.get("used_quota", 0)
                    account.cached_request_count = user_info.get("request_count", 0)
                    account.cached_user_group = user_info.get("group", "default")
                    account.cached_aff_code = user_info.get("aff_code")
                    account.cached_aff_count = user_info.get("aff_count", 0)
                    account.cached_aff_history_quota = user_info.get("aff_history_quota", 0)
                    account.quota_updated_at = now
                    healthy_count += 1
                else:
                    account.health_status = "unhealthy"
                    account.health_message = user_info.get("message", "凭证验证失败")
                    unhealthy_count += 1
                    logger.warning(f"账号 {account.username} 健康检查失败: {account.health_message}")

                account.last_health_check = now
                if previous_status != account.health_status:
                    health_events.append({
                        "account_id": account.id,
                        "username": account.username or "",
                        "health_status": account.health_status,
                        "health_message": account.health_message,
                        "previous_status": previous_status,
                    })

            except Exception as e:
                logger.error(f"账号 {account.username} 健康检查异常: {e}")
                previous_status = account.health_status or "unknown"
                account.health_status = "unhealthy"
                account.health_message = str(e)
                account.last_health_check = datetime.now()
                unhealthy_count += 1
                if previous_status != account.health_status:
                    health_events.append({
                        "account_id": account.id,
                        "username": account.username or "",
                        "health_status": account.health_status,
                        "health_message": account.health_message,
                        "previous_status": previous_status,
                    })

        db.commit()
        for payload in health_events:
            publish_event("health_changed", payload)
        logger.info(f"健康检查完成: 健康 {healthy_count}, 异常 {unhealthy_count}")

        unhealthy_accounts = db.query(Account).filter(
            Account.is_active == True,
            Account.health_status == "unhealthy"
        ).all()

        for account in unhealthy_accounts:
            send_health_alert_for_account(db, account)

    except Exception as e:
        logger.error(f"健康检查任务异常: {e}")
    finally:
        db.close()


def send_health_alert_for_account(db, account):
    """发送单个账号的健康检查告警通知（按账号配置的推送渠道）"""
    from app.models import AccountNotify

    try:
        account_notifies = db.query(AccountNotify).filter(
            AccountNotify.account_id == account.id,
            AccountNotify.is_enabled == True
        ).all()

        if not account_notifies:
            return

        channel_ids = [n.channel_id for n in account_notifies]
        channels = db.query(NotifyChannel).filter(
            NotifyChannel.id.in_(channel_ids),
            NotifyChannel.is_enabled == True
        ).all()

        if not channels:
            return

        title = f"账号健康告警 - {account.username}"
        content = f"账号 {account.username} 凭证异常: {account.health_message or '未知错误'}\n请及时更新 Session Cookie。"

        account_notify_map = {n.channel_id: n for n in account_notifies}

        for channel in channels:
            try:
                config = json.loads(channel.config)
                account_notify = account_notify_map.get(channel.id)
                account_config = json.loads(account_notify.notify_config) if account_notify and account_notify.notify_config else {}
                merged_config = {
                    **_global_channel_config(channel.type, config),
                    **account_config
                }

                notifier = NotifyFactory.create(channel.type, config)
                result = notifier.send(title, content, merged_config)
                if result:
                    logger.info(f"健康告警发送成功: {channel.name} -> {account.username}")
                else:
                    logger.error(f"健康告警发送失败: {channel.name} -> {account.username}")
            except Exception as e:
                logger.error(f"发送健康告警失败 {channel.name}: {e}")
    except Exception as e:
        logger.error(f"发送健康告警异常: {e}")


def update_health_check_schedule():
    """更新健康检查定时任务"""
    db = SessionLocal()

    try:
        enabled = get_setting_value(db, "health_check_enabled", True)
        interval_hours = get_setting_value(db, "health_check_interval", 6)

        if scheduler.get_job("health_check"):
            scheduler.remove_job("health_check")

        if enabled:
            scheduler.add_job(
                health_check_job,
                IntervalTrigger(hours=interval_hours),
                id="health_check",
                replace_existing=True
            )
            logger.info(f"健康检查任务已设置: 每 {interval_hours} 小时")
        else:
            logger.info("健康检查任务已禁用")

    except Exception as e:
        logger.error(f"更新健康检查定时任务失败: {e}")
    finally:
        db.close()


def log_cleanup_job():
    """按保留天数清理审计日志和日志文件"""
    from app.services.log_cleanup import cleanup_audit_logs, cleanup_log_files, format_size

    db = SessionLocal()

    try:
        audit_days = get_setting_value(db, "audit_log_retention_days", 0)
        system_days = get_setting_value(db, "system_log_retention_days", 0)

        # 0 表示不自动清理；这里只按天保留，不做"全部清空"
        if audit_days and audit_days > 0:
            deleted = cleanup_audit_logs(db, audit_days)
            logger.info(f"审计日志保留清理完成: 保留 {audit_days} 天，删除 {deleted} 条")

        if system_days and system_days > 0:
            result = cleanup_log_files(system_days)
            logger.info(
                f"系统日志保留清理完成: 保留 {system_days} 天，"
                f"删除 {result['removed_files']} 个归档，释放 {format_size(result['freed_bytes'])}"
            )

    except Exception as e:
        logger.error(f"日志保留清理失败: {e}")
    finally:
        db.close()


def update_log_cleanup_schedule():
    """更新日志清理定时任务"""
    db = SessionLocal()

    try:
        audit_days = get_setting_value(db, "audit_log_retention_days", 0)
        system_days = get_setting_value(db, "system_log_retention_days", 0)

        if scheduler.get_job("log_cleanup"):
            scheduler.remove_job("log_cleanup")

        if (audit_days and audit_days > 0) or (system_days and system_days > 0):
            # 凌晨低峰执行；避开整点，且重启不会立刻触发一次清理
            scheduler.add_job(
                log_cleanup_job,
                CronTrigger(hour=3, minute=17),
                id="log_cleanup",
                replace_existing=True
            )
            logger.info(
                f"日志清理任务已设置: 每天 03:17（审计 {audit_days or '关闭'} 天 / 系统 {system_days or '关闭'} 天）"
            )
        else:
            logger.info("日志清理任务已禁用")

    except Exception as e:
        logger.error(f"更新日志清理定时任务失败: {e}")
    finally:
        db.close()


def init_scheduler():
    """初始化调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("调度器已启动")

    update_sign_schedule()
    update_health_check_schedule()
    update_log_cleanup_schedule()


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")
