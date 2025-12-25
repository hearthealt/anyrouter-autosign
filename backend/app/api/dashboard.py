"""
仪表盘 API
"""
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Account, SignLog
from app.schemas import ApiResponse, DashboardResponse, RecentSign
from app.services import anyrouter_service
from app.utils import format_quota

router = APIRouter(tags=["仪表盘"])


@router.get("/dashboard", response_model=ApiResponse)
def get_dashboard(db: Session = Depends(get_db)):
    """获取仪表盘数据"""
    # 账号统计
    account_count = db.query(Account).count()
    active_account_count = db.query(Account).filter(Account.is_active == True).count()

    # 今日签到统计
    today = date.today()
    today_logs = db.query(SignLog).filter(
        func.date(SignLog.sign_time) == today
    ).all()

    today_sign_count = len(today_logs)
    today_sign_success = len([log for log in today_logs if log.success])

    # 获取所有账号的配额信息
    accounts = db.query(Account).filter(Account.is_active == True).all()
    total_quota = 0
    total_used_quota = 0
    total_request_count = 0

    for account in accounts:
        if not account.anyrouter_user_id:
            continue
        try:
            success, info = anyrouter_service.get_user_info(
                account.session_cookie,
                str(account.anyrouter_user_id)
            )
            if success:
                total_quota += info.get("quota", 0)
                total_used_quota += info.get("used_quota", 0)
                total_request_count += info.get("request_count", 0)
        except:
            pass

    # 最近签到记录
    recent_logs = db.query(SignLog, Account).join(
        Account, Account.id == SignLog.account_id
    ).order_by(SignLog.sign_time.desc()).limit(10).all()

    recent_signs = [
        RecentSign(
            username=account.username or "",
            sign_time=log.sign_time.strftime("%Y-%m-%d %H:%M:%S"),
            success=log.success
        )
        for log, account in recent_logs
    ]

    return ApiResponse(
        success=True,
        data=DashboardResponse(
            account_count=account_count,
            active_account_count=active_account_count,
            today_sign_count=today_sign_count,
            today_sign_success=today_sign_success,
            total_quota=total_quota,
            total_used_quota=total_used_quota,
            total_quota_display=format_quota(total_quota),
            total_used_quota_display=format_quota(total_used_quota),
            total_request_count=total_request_count,
            recent_signs=recent_signs
        )
    )
