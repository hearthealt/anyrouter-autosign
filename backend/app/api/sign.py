"""
签到 API
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, SignLog, NotifyChannel, AccountNotify
from app.schemas import (
    SignResult, SignLogResponse, BatchSignResult, BatchSignResponse, ApiResponse
)
from app.services import anrouter_service, execute_with_session_refresh, NotifyFactory
from app.services.events import publish_event
from app.utils import format_quota, get_account_platform_config

router = APIRouter(tags=["签到"])


def send_notifications(db: Session, account: Account, title: str, content: str):
    """发送推送通知"""
    notify_configs = db.query(AccountNotify, NotifyChannel).join(
        NotifyChannel, NotifyChannel.id == AccountNotify.channel_id
    ).filter(
        AccountNotify.account_id == account.id,
        AccountNotify.is_enabled == True,
        NotifyChannel.is_enabled == True
    ).all()

    for account_notify, channel in notify_configs:
        try:
            config = json.loads(channel.config)
            account_config = json.loads(account_notify.notify_config) if account_notify.notify_config else {}
            merged_config = {**config, **account_config}

            notifier = NotifyFactory.create(channel.type, config)
            notifier.send(title, content, merged_config)
        except Exception as e:
            pass  # 静默失败，不影响主流程


def build_success_notification_content(reward_quota: int) -> str:
    """构造签到成功通知文案。"""
    if reward_quota > 0:
        return f"获得 {format_quota(reward_quota)}，祝您使用愉快！"
    return "签到成功"


def perform_sign_request(db: Session, account: Account, platform_config: dict):
    """执行签到请求，必要时自动刷新 session 后重试。"""
    return execute_with_session_refresh(
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


@router.post("/accounts/{account_id}/sign", response_model=ApiResponse)
def sign_account(account_id: int, db: Session = Depends(get_db)):
    """单账号签到"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.is_active:
        raise HTTPException(status_code=400, detail="账号已禁用")

    if not account.anrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")
    if not account.platform_id or not account.platform:
        raise HTTPException(status_code=400, detail="账号未配置平台")

    platform_config = get_account_platform_config(account)

    # 执行签到
    success, result = perform_sign_request(db, account, platform_config)

    sign_success = success and result.get("success", False)
    message = result.get("message", "")
    reward_quota = result.get("reward_quota", 0)
    already_signed = bool(result.get("already_signed", False))

    if already_signed:
        log_message = "今日已签到"
        log_status = "already_signed"
    elif sign_success:
        log_message = message
        log_status = "success"
    else:
        log_message = message
        log_status = "failed"

    log = SignLog(
        account_id=account.id,
        success=sign_success,
        message=log_message,
        reward_quota=reward_quota,
        retry_count=0,
        status=log_status
    )
    db.add(log)
    db.commit()

    if sign_success and not already_signed:
        title = f"{account.username} 签到成功"
        content = build_success_notification_content(reward_quota)
        send_notifications(db, account, title, content)
    elif not sign_success:
        title = f"{account.username} 签到失败"
        content = f"原因: {message}"
        send_notifications(db, account, title, content)

    if already_signed:
        return_message = "今日已签到"
        status = "already_signed"
    elif sign_success:
        return_message = message or "签到成功"
        status = "success"
    else:
        return_message = message or "签到失败"
        status = "failed"

    publish_event(
        "sign_completed",
        {
            "account_id": account.id,
            "username": account.username or "",
            "success": sign_success,
            "already_signed": already_signed,
            "message": return_message,
            "reward_quota": reward_quota,
            "reward_display": format_quota(reward_quota),
        }
    )

    return ApiResponse(
        success=True,
        message=return_message,
        data=SignResult(
            reward_quota=reward_quota,
            reward_display=format_quota(reward_quota),
            message=return_message,
            sign_time=datetime.now(),
            status=status
        )
    )


@router.post("/sign/batch", response_model=ApiResponse)
def batch_sign(db: Session = Depends(get_db)):
    """批量签到所有启用账号"""
    accounts = db.query(Account).filter(
        Account.is_active == True,
        Account.anrouter_user_id.isnot(None),
        Account.platform_id.isnot(None)
    ).all()

    results = []
    success_count = 0
    fail_count = 0
    already_signed_count = 0

    for account in accounts:
        platform_config = get_account_platform_config(account)

        success, result = perform_sign_request(db, account, platform_config)
        sign_success = success and result.get("success", False)
        message = result.get("message", "")
        reward_quota = result.get("reward_quota", 0)
        already_signed = bool(result.get("already_signed", False))

        if already_signed:
            log_message = "今日已签到"
            log_status = "already_signed"
        elif sign_success:
            log_message = message
            log_status = "success"
        else:
            log_message = message
            log_status = "failed"

        log = SignLog(
            account_id=account.id,
            success=sign_success,
            message=log_message,
            reward_quota=reward_quota,
            retry_count=0,
            status=log_status
        )
        db.add(log)

        if sign_success and not already_signed:
            title = f"{account.username} 签到成功"
            content = build_success_notification_content(reward_quota)
            send_notifications(db, account, title, content)
            success_count += 1
        elif already_signed:
            already_signed_count += 1
        else:
            title = f"{account.username} 签到失败"
            content = f"原因: {message}"
            send_notifications(db, account, title, content)
            fail_count += 1

        if already_signed:
            result_message = "今日已签到"
        elif sign_success:
            result_message = message or "签到成功"
        else:
            result_message = message or "签到失败"

        results.append(BatchSignResult(
            account_id=account.id,
            username=account.username or "",
            success=sign_success,
            message=result_message
        ))

    db.commit()

    for account, result_item in zip(accounts, results):
        publish_event(
            "sign_completed",
            {
                "account_id": account.id,
                "username": account.username or "",
                "success": result_item.success,
                "already_signed": result_item.message == "今日已签到",
                "message": result_item.message,
                "reward_quota": 0,
                "reward_display": format_quota(0),
            }
        )

    return ApiResponse(
        success=True,
        message=f"批量签到完成：成功 {success_count}，已签到 {already_signed_count}，失败 {fail_count}",
        data=BatchSignResponse(
            total=len(accounts),
            success_count=success_count,
            fail_count=fail_count,
            already_signed_count=already_signed_count,
            results=results
        )
    )


@router.get("/sign-logs", response_model=ApiResponse)
def get_all_sign_logs(
    page: int = 1,
    size: int = 20,
    account_id: int = None,
    success: bool = None,
    start_date: str = None,
    end_date: str = None,
    sort_by: str = "sign_time",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """获取所有签到日志"""

    def build_base_query():
        """构建基础查询条件"""
        q = db.query(SignLog).join(Account, Account.id == SignLog.account_id)
        if account_id:
            q = q.filter(SignLog.account_id == account_id)
        if start_date:
            q = q.filter(SignLog.sign_time >= datetime.fromisoformat(start_date))
        if end_date:
            q = q.filter(SignLog.sign_time < datetime.fromisoformat(end_date + " 23:59:59"))
        return q

    query = db.query(SignLog, Account).join(Account, Account.id == SignLog.account_id)
    if account_id:
        query = query.filter(SignLog.account_id == account_id)
    if success is not None:
        query = query.filter(SignLog.success == success)
    if start_date:
        query = query.filter(SignLog.sign_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(SignLog.sign_time < datetime.fromisoformat(end_date + " 23:59:59"))

    stats_query = build_base_query()
    if success is not None:
        stats_query = stats_query.filter(SignLog.success == success)

    total = query.count()
    success_count = stats_query.filter(SignLog.success == True).count()
    fail_count = stats_query.filter(SignLog.success == False).count()

    normalized_order = (sort_order or "desc").lower()
    is_desc = normalized_order.startswith("desc")

    if sort_by == "username":
        sort_column = Account.username
    elif sort_by == "status":
        sort_column = SignLog.status
    elif sort_by == "reward":
        sort_column = SignLog.reward_quota
    else:
        sort_column = SignLog.sign_time

    offset = (page - 1) * size
    logs = query.order_by(
        desc(sort_column) if is_desc else asc(sort_column),
        SignLog.id.desc()
    ).offset(offset).limit(size).all()

    items = [
        {
            "id": log.id,
            "account_id": log.account_id,
            "username": account.username,
            "sign_time": log.sign_time,
            "success": log.success,
            "message": log.message,
            "reward_quota": log.reward_quota,
            "reward_display": format_quota(log.reward_quota),
            "retry_count": log.retry_count,
            "status": log.status
        }
        for log, account in logs
    ]

    return ApiResponse(success=True, data={
        "items": items,
        "total": total,
        "success_count": success_count,
        "fail_count": fail_count,
        "page": page,
        "size": size
    })


@router.get("/accounts/{account_id}/sign-logs", response_model=ApiResponse)
def get_sign_logs(
    account_id: int,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db)
):
    """获取签到历史"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    total = db.query(SignLog).filter(SignLog.account_id == account_id).count()

    offset = (page - 1) * size
    logs = db.query(SignLog).filter(
        SignLog.account_id == account_id
    ).order_by(SignLog.sign_time.desc()).offset(offset).limit(size).all()

    items = [
        SignLogResponse(
            id=log.id,
            account_id=log.account_id,
            sign_time=log.sign_time,
            success=log.success,
            message=log.message,
            reward_quota=log.reward_quota,
            reward_display=format_quota(log.reward_quota),
            retry_count=log.retry_count,
            status=log.status
        )
        for log in logs
    ]

    return ApiResponse(success=True, data={
        "items": items,
        "total": total,
        "page": page,
        "size": size
    })
