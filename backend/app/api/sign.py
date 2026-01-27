"""
签到 API
"""
import json
import re
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, SignLog, NotifyChannel, AccountNotify
from app.schemas import (
    SignResult, SignLogResponse, BatchSignResult, BatchSignResponse, ApiResponse
)
from app.services import anyrouter_service, NotifyFactory
from app.utils import format_quota
from app.config import settings

router = APIRouter(tags=["签到"])


def send_notifications(db: Session, account: Account, title: str, content: str):
    """发送推送通知"""
    # 获取账号关联的推送渠道
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
            # 合并配置：账号配置优先，渠道配置作为后备
            merged_config = {**config, **account_config}

            notifier = NotifyFactory.create(channel.type, config)
            notifier.send(title, content, merged_config)
        except Exception as e:
            pass  # 静默失败，不影响主流程


@router.post("/accounts/{account_id}/sign", response_model=ApiResponse)
def sign_account(account_id: int, db: Session = Depends(get_db)):
    """单账号签到"""
    account = db.query(Account).filter(Account.id == account_id).first()

    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    if not account.is_active:
        raise HTTPException(status_code=400, detail="账号已禁用")

    if not account.anyrouter_user_id:
        raise HTTPException(status_code=400, detail="账号缺少 user_id")

    # 执行签到
    success, result = anyrouter_service.sign_in(
        account.session_cookie,
        str(account.anyrouter_user_id)
    )

    sign_success = success and result.get("success", False)
    message = result.get("message", "")
    reward_quota = 0

    # 判断签到状态：success=true 且 message 为空表示今日已签到
    already_signed = sign_success and not message

    # 解析奖励配额（message 中的数字是美元值，需要转换为原始配额）
    if sign_success and message:
        match = re.search(r'\$(\d+(?:\.\d+)?)', message)
        if match:
            usd_value = float(match.group(1))
            reward_quota = int(usd_value * settings.quota_to_usd_rate)

    # 记录签到日志
    if already_signed:
        log_message = "今日已签到"
    else:
        log_message = message

    log = SignLog(
        account_id=account.id,
        success=sign_success,
        message=log_message,
        reward_quota=reward_quota
    )
    db.add(log)
    db.commit()

    # 发送通知（已签到的不发通知）
    if sign_success and not already_signed:
        title = f"{account.username} 签到成功"
        content = f"获得 {format_quota(reward_quota)}，祝您使用愉快！"
        send_notifications(db, account, title, content)
    elif not sign_success:
        title = f"{account.username} 签到失败"
        content = f"原因: {message}"
        send_notifications(db, account, title, content)

    # 返回结果
    if already_signed:
        return_message = "今日已签到"
    elif sign_success:
        return_message = message or "签到成功"
    else:
        return_message = "签到失败"

    return ApiResponse(
        success=True,
        message=return_message,
        data=SignResult(
            reward_quota=reward_quota,
            reward_display=format_quota(reward_quota),
            message=return_message,
            sign_time=datetime.now()
        )
    )


@router.post("/sign/batch", response_model=ApiResponse)
def batch_sign(db: Session = Depends(get_db)):
    """批量签到所有启用账号"""
    accounts = db.query(Account).filter(
        Account.is_active == True,
        Account.anyrouter_user_id.isnot(None)
    ).all()

    results = []
    success_count = 0
    fail_count = 0
    already_signed_count = 0

    for account in accounts:
        success, result = anyrouter_service.sign_in(
            account.session_cookie,
            str(account.anyrouter_user_id)
        )
        sign_success = success and result.get("success", False)
        message = result.get("message", "")
        reward_quota = 0

        # 判断签到状态
        already_signed = sign_success and not message

        if sign_success and message:
            match = re.search(r'\$(\d+(?:\.\d+)?)', message)
            if match:
                usd_value = float(match.group(1))
                reward_quota = int(usd_value * settings.quota_to_usd_rate)

        # 记录日志
        if already_signed:
            log_message = "今日已签到"
        else:
            log_message = message

        log = SignLog(
            account_id=account.id,
            success=sign_success,
            message=log_message,
            reward_quota=reward_quota
        )
        db.add(log)

        # 发送通知（已签到的不发通知）
        if sign_success and not already_signed:
            title = f"{account.username} 签到成功"
            content = f"获得 {format_quota(reward_quota)}"
            send_notifications(db, account, title, content)
            success_count += 1
        elif already_signed:
            already_signed_count += 1
        else:
            title = f"{account.username} 签到失败"
            content = f"原因: {message}"
            send_notifications(db, account, title, content)
            fail_count += 1

        # 结果消息
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

    return ApiResponse(
        success=True,
        message=f"批量签到完成：成功 {success_count}，已签到 {already_signed_count}，失败 {fail_count}",
        data=BatchSignResponse(
            total=len(accounts),
            success_count=success_count,
            fail_count=fail_count,
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

    # 构建主查询（用于分页和统计）
    query = db.query(SignLog, Account).join(Account, Account.id == SignLog.account_id)
    if account_id:
        query = query.filter(SignLog.account_id == account_id)
    if success is not None:
        query = query.filter(SignLog.success == success)
    if start_date:
        query = query.filter(SignLog.sign_time >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(SignLog.sign_time < datetime.fromisoformat(end_date + " 23:59:59"))

    # 计算统计数据（基于过滤条件）
    stats_query = build_base_query()
    if success is not None:
        stats_query = stats_query.filter(SignLog.success == success)

    total = query.count()
    success_count = stats_query.filter(SignLog.success == True).count()
    fail_count = stats_query.filter(SignLog.success == False).count()

    offset = (page - 1) * size
    logs = query.order_by(SignLog.sign_time.desc()).offset(offset).limit(size).all()

    items = [
        {
            "id": log.id,
            "account_id": log.account_id,
            "username": account.username,
            "sign_time": log.sign_time,
            "success": log.success,
            "message": log.message,
            "reward_quota": log.reward_quota,
            "reward_display": format_quota(log.reward_quota)
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

    # 获取总数
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
            reward_display=format_quota(log.reward_quota)
        )
        for log in logs
    ]

    return ApiResponse(success=True, data={
        "items": items,
        "total": total,
        "page": page,
        "size": size
    })
