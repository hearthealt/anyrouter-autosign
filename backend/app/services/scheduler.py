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
from app.services import anrouter_service, execute_with_session_refresh
from app.services.events import publish_event
from app.services.notify import NotifyFactory
from app.utils import format_quota, get_account_platform_config

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


def send_sign_notification(db, account, success: bool, sign_message: str):
    """发送单个账号的签到通知"""
    from app.models import AccountNotify

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

    title = f"签到{'成功' if success else '失败'} - {account.username}"
    content = sign_message

    account_notify_map = {n.channel_id: n for n in account_notifies}

    for channel in channels:
        try:
            config = json.loads(channel.config)
            account_notify = account_notify_map.get(channel.id)
            account_config = json.loads(account_notify.notify_config) if account_notify and account_notify.notify_config else {}
            merged_config = {**config, **account_config}

            notifier = NotifyFactory.create(channel.type, config)
            result = notifier.send(title, content, merged_config)
            if result:
                logger.info(f"通知发送成功: {channel.name} -> {account.username}")
            else:
                logger.error(f"通知发送失败: {channel.name} -> {account.username}")
        except Exception as e:
            logger.error(f"通知发送异常 {channel.name}: {e}")


def execute_sign(db, account) -> dict:
    """执行单个账号签到并返回统一结果。"""
    platform_config = get_account_platform_config(account)
    request_success, result = execute_with_session_refresh(
        db,
        account,
        lambda session_cookie, user_id, current_platform: anrouter_service.sign_in(
            session_cookie,
            user_id,
            current_platform["base_url"],
            sign_api=current_platform["sign_api"],
            checkin_api=current_platform["checkin_api"],
            console_url=current_platform["console_url"]
        ),
        platform_config=platform_config,
    )

    if not request_success:
        return {
            "success": False,
            "already_signed": False,
            "message": result.get("message", "签到失败"),
            "reward_quota": 0,
        }

    return {
        "success": bool(result.get("success", False)),
        "already_signed": bool(result.get("already_signed", False)),
        "message": result.get("message", ""),
        "reward_quota": result.get("reward_quota", 0),
    }


def build_sign_message(message: str, reward_quota: int, already_signed: bool = False) -> str:
    """构造用于日志和通知的签到结果文案。"""
    if already_signed:
        return "今日已签到"
    if reward_quota > 0:
        base_message = message or "签到成功"
        return f"{base_message}，获得 {format_quota(reward_quota)}"
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

        accounts = db.query(Account).filter(
            Account.is_active == True,
            Account.anrouter_user_id.isnot(None),
            Account.platform_id.isnot(None)
        ).all()

        if not accounts:
            logger.info("没有可签到的账号")
            return

        retry_enabled = get_setting_value(db, "sign_retry_enabled", True)
        max_retries = get_setting_value(db, "sign_max_retries", 3)
        retry_interval = get_setting_value(db, "sign_retry_interval", 30)

        success_count = 0
        fail_count = 0
        skip_count = 0
        retry_accounts = []
        event_payloads = []

        for account in accounts:
            try:
                result = execute_sign(db, account)
                sign_success = result["success"]
                already_signed = result["already_signed"]
                message = result["message"]
                reward_quota = result["reward_quota"]

                if already_signed:
                    log_message = "今日已签到"
                    log_status = "already_signed"
                    skip_count += 1
                else:
                    log_message = build_sign_message(message, reward_quota)
                    log_status = "success" if sign_success else "failed"
                    if sign_success:
                        success_count += 1
                    else:
                        fail_count += 1

                log = SignLog(
                    account_id=account.id,
                    success=sign_success,
                    message=log_message,
                    reward_quota=reward_quota,
                    retry_count=0,
                    status=log_status
                )
                db.add(log)
                db.flush()

                logger.info(f"账号 {account.username} 签到: {log_message}")

                if not already_signed:
                    send_sign_notification(db, account, sign_success, log_message)
                if retry_enabled and not sign_success and not already_signed:
                    retry_accounts.append({
                        "account_id": account.id,
                        "retry_count": 0,
                        "log_id": log.id,
                    })

                event_payloads.append({
                    "account_id": account.id,
                    "username": account.username or "",
                    "success": sign_success,
                    "already_signed": already_signed,
                    "message": log_message,
                    "reward_quota": reward_quota,
                    "reward_display": format_quota(reward_quota),
                })

            except Exception as e:
                logger.error(f"账号 {account.username} 签到异常: {e}")
                fail_count += 1
                send_sign_notification(db, account, False, str(e))
                if retry_enabled:
                    retry_accounts.append({
                        "account_id": account.id,
                        "retry_count": 0
                    })
                event_payloads.append({
                    "account_id": account.id,
                    "username": account.username or "",
                    "success": False,
                    "already_signed": False,
                    "message": str(e),
                    "reward_quota": 0,
                    "reward_display": format_quota(0),
                })

        db.commit()
        for payload in event_payloads:
            publish_event("sign_completed", payload)
        logger.info(f"自动签到完成: 成功 {success_count}, 已签 {skip_count}, 失败 {fail_count}")

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
    """重试签到任务"""
    logger.info(f"开始执行重试签到任务，共 {len(accounts)} 个账号...")
    db = SessionLocal()

    try:
        success_count = 0
        fail_count = 0
        retry_accounts = []
        event_payloads = []

        for item in accounts:
            account_id = item["account_id"]
            retry_count = item["retry_count"] + 1
            log_id = item.get("log_id")

            account = db.query(Account).filter(
                Account.id == account_id,
                Account.is_active == True
            ).first()

            if not account or not account.anrouter_user_id or not account.platform_id:
                continue

            try:
                result = execute_sign(db, account)
                sign_success = result["success"]
                already_signed = result["already_signed"]
                message = result["message"]
                reward_quota = result["reward_quota"]
                log = db.query(SignLog).filter(SignLog.id == log_id).first() if log_id else None

                if already_signed:
                    log_message = f"重试{retry_count}次后: 今日已签到"
                    log_status = "already_signed"
                    success_count += 1
                elif sign_success:
                    log_message = f"重试{retry_count}次后: {build_sign_message(message, reward_quota)}"
                    log_status = "success"
                    success_count += 1
                else:
                    log_message = f"重试{retry_count}次后: {message}"
                    log_status = "failed"
                    fail_count += 1
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
                    log.retry_count = retry_count
                    log.status = log_status
                else:
                    log = SignLog(
                        account_id=account.id,
                        success=sign_success,
                        message=log_message,
                        reward_quota=reward_quota,
                        retry_count=retry_count,
                        status=log_status
                    )
                    db.add(log)
                    db.flush()
                    log_id = log.id

                logger.info(f"账号 {account.username} 重试签到(第{retry_count}次): {log_message}")

                if sign_success and not already_signed:
                    send_sign_notification(
                        db,
                        account,
                        True,
                        f"重试签到成功: {build_sign_message(message, reward_quota)}"
                    )
                event_payloads.append({
                    "account_id": account.id,
                    "username": account.username or "",
                    "success": sign_success,
                    "already_signed": already_signed,
                    "message": log_message,
                    "reward_quota": reward_quota,
                    "reward_display": format_quota(reward_quota),
                })

            except Exception as e:
                logger.error(f"账号 {account.username} 重试签到异常: {e}")
                fail_count += 1
                log = db.query(SignLog).filter(SignLog.id == log_id).first() if log_id else None
                if log:
                    log.sign_time = datetime.now()
                    log.success = False
                    log.message = f"重试{retry_count}次后: {e}"
                    log.reward_quota = 0
                    log.retry_count = retry_count
                    log.status = "failed"
                else:
                    log = SignLog(
                        account_id=account.id,
                        success=False,
                        message=f"重试{retry_count}次后: {e}",
                        reward_quota=0,
                        retry_count=retry_count,
                        status="failed"
                    )
                    db.add(log)
                    db.flush()
                    log_id = log.id
                if retry_count < max_retries:
                    retry_accounts.append({
                        "account_id": account_id,
                        "retry_count": retry_count,
                        "log_id": log_id,
                    })
                event_payloads.append({
                    "account_id": account.id,
                    "username": account.username or "",
                    "success": False,
                    "already_signed": False,
                    "message": str(e),
                    "reward_quota": 0,
                    "reward_display": format_quota(0),
                })

        db.commit()
        for payload in event_payloads:
            publish_event("sign_completed", payload)
        logger.info(f"重试签到完成: 成功 {success_count}, 失败 {fail_count}")

        if retry_accounts:
            schedule_retry_sign(retry_accounts, max_retries, retry_interval)

    except Exception as e:
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
                        console_url=current_platform["console_url"]
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
                merged_config = {**config, **account_config}

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


def init_scheduler():
    """初始化调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("调度器已启动")

    update_sign_schedule()
    update_health_check_schedule()


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")
