"""
仪表盘 API
"""
from datetime import date, datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Account, SignLog
from app.schemas import ApiResponse, DashboardResponse, RecentSign, DailyTrend
from app.utils import format_quota

router = APIRouter(tags=["仪表盘"])


@router.get("/dashboard", response_model=ApiResponse)
def get_dashboard(db: Session = Depends(get_db)):
    """获取仪表盘数据"""
    # 账号统计
    account_count = db.query(Account).count()
    active_account_count = db.query(Account).filter(Account.is_active == True).count()
    unhealthy_account_count = db.query(Account).filter(Account.health_status == "unhealthy").count()

    # 今日签到统计
    today = date.today()
    today_logs = db.query(SignLog).filter(
        func.date(SignLog.sign_time) == today
    ).all()

    today_sign_count = len(today_logs)
    today_sign_success = len([log for log in today_logs if log.success])

    # 本月奖励统计
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_reward = db.query(func.sum(SignLog.reward_quota)).filter(
        SignLog.success == True,
        SignLog.sign_time >= month_start
    ).scalar() or 0

    # 总体成功率
    all_logs_count = db.query(SignLog).count()
    all_success_count = db.query(SignLog).filter(SignLog.success == True).count()
    success_rate = round(all_success_count / all_logs_count * 100, 1) if all_logs_count > 0 else 0

    # 从缓存获取所有账号的配额信息（不再实时请求API）
    quota_stats = db.query(
        func.sum(Account.cached_quota),
        func.sum(Account.cached_used_quota),
        func.sum(Account.cached_request_count)
    ).filter(Account.is_active == True).first()

    total_quota = quota_stats[0] or 0
    total_used_quota = quota_stats[1] or 0
    total_request_count = quota_stats[2] or 0

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

    # 7天签到趋势
    daily_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_logs = db.query(SignLog).filter(
            func.date(SignLog.sign_time) == day
        ).all()
        success_count = len([log for log in day_logs if log.success])
        fail_count = len(day_logs) - success_count
        daily_trend.append(DailyTrend(
            date=day.strftime("%m-%d"),
            success=success_count,
            fail=fail_count
        ))

    return ApiResponse(
        success=True,
        data=DashboardResponse(
            account_count=account_count,
            active_account_count=active_account_count,
            unhealthy_account_count=unhealthy_account_count,
            today_sign_count=today_sign_count,
            today_sign_success=today_sign_success,
            total_quota=total_quota,
            total_used_quota=total_used_quota,
            total_quota_display=format_quota(total_quota),
            total_used_quota_display=format_quota(total_used_quota),
            total_request_count=total_request_count,
            month_reward=month_reward,
            month_reward_display=format_quota(month_reward),
            success_rate=success_rate,
            recent_signs=recent_signs,
            daily_trend=daily_trend
        )
    )
