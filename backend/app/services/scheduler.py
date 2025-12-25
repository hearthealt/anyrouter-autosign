"""
定时任务调度器
"""
import json
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models import Account, SignLog, Setting, NotifyChannel
from app.services import anyrouter_service
from app.services.notify import NotifyFactory
from app.utils import format_quota

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

    # 获取账号的推送配置
    account_notifies = db.query(AccountNotify).filter(
        AccountNotify.account_id == account.id,
        AccountNotify.is_enabled == True
    ).all()

    if not account_notifies:
        return

    # 获取渠道配置
    channel_ids = [n.channel_id for n in account_notifies]
    channels = db.query(NotifyChannel).filter(
        NotifyChannel.id.in_(channel_ids),
        NotifyChannel.is_enabled == True
    ).all()

    if not channels:
        return

    # 构建通知内容
    title = f"签到{'成功' if success else '失败'} - {account.username}"
    content = sign_message

    # 发送通知
    for channel in channels:
        try:
            config = json.loads(channel.config)
            notifier = NotifyFactory.create(channel.type, config)
            result = notifier.send(title, content, config)
            if result:
                logger.info(f"通知发送成功: {channel.name} -> {account.username}")
            else:
                logger.error(f"通知发送失败: {channel.name} -> {account.username}")
        except Exception as e:
            logger.error(f"通知发送异常 {channel.name}: {e}")


def auto_sign_job():
    """自动签到任务"""
    logger.info("开始执行自动签到任务...")
    db = SessionLocal()

    try:
        # 检查是否启用自动签到
        enabled = get_setting_value(db, "auto_sign_enabled", False)
        if not enabled:
            logger.info("自动签到未启用，跳过")
            return

        # 获取所有启用的账号
        accounts = db.query(Account).filter(
            Account.is_active == True,
            Account.anyrouter_user_id.isnot(None)
        ).all()

        if not accounts:
            logger.info("没有可签到的账号")
            return

        success_count = 0
        fail_count = 0
        skip_count = 0

        for account in accounts:
            try:
                # 执行签到
                success, result = anyrouter_service.sign_in(
                    account.session_cookie,
                    str(account.anyrouter_user_id)
                )

                sign_success = success and result.get("success", False)
                message = result.get("message", "")
                reward_quota = 0

                # 判断是否已签到
                already_signed = sign_success and not message

                if sign_success and message:
                    import re
                    match = re.search(r'(\d+)', message)
                    if match:
                        reward_quota = int(match.group(1))

                # 记录日志
                if already_signed:
                    log_message = "今日已签到"
                    skip_count += 1
                else:
                    log_message = message
                    if sign_success:
                        success_count += 1
                    else:
                        fail_count += 1

                log = SignLog(
                    account_id=account.id,
                    success=sign_success,
                    message=log_message,
                    reward_quota=reward_quota
                )
                db.add(log)

                logger.info(f"账号 {account.username} 签到: {log_message}")

                # 发送该账号的通知（跳过已签到的）
                if not already_signed:
                    send_sign_notification(db, account, sign_success, log_message)

            except Exception as e:
                logger.error(f"账号 {account.username} 签到异常: {e}")
                fail_count += 1
                # 发送失败通知
                send_sign_notification(db, account, False, str(e))

        db.commit()
        logger.info(f"自动签到完成: 成功 {success_count}, 已签 {skip_count}, 失败 {fail_count}")

    except Exception as e:
        logger.error(f"自动签到任务异常: {e}")
    finally:
        db.close()


def update_sign_schedule():
    """更新签到定时任务"""
    db = SessionLocal()

    try:
        enabled = get_setting_value(db, "auto_sign_enabled", False)
        sign_time = get_setting_value(db, "auto_sign_time", "08:00")

        # 移除现有任务
        if scheduler.get_job("auto_sign"):
            scheduler.remove_job("auto_sign")

        if enabled and sign_time:
            hour, minute = map(int, sign_time.split(":"))

            # 添加定时任务
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


def init_scheduler():
    """初始化调度器"""
    if not scheduler.running:
        scheduler.start()
        logger.info("调度器已启动")

    # 初始化签到任务
    update_sign_schedule()


def shutdown_scheduler():
    """关闭调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("调度器已关闭")
