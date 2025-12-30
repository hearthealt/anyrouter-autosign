"""
签到统计 API
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, and_, extract
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, SignLog
from app.schemas import ApiResponse
from app.utils import format_quota

router = APIRouter(prefix="/statistics", tags=["统计"])


@router.get("/overview", response_model=ApiResponse)
def get_overview(db: Session = Depends(get_db)):
    """获取统计概览"""
    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 总账号数
    total_accounts = db.query(Account).count()
    active_accounts = db.query(Account).filter(Account.is_active == True).count()

    # 今日签到
    today_logs = db.query(SignLog).filter(SignLog.sign_time >= today).all()
    today_success = sum(1 for log in today_logs if log.success)
    today_fail = len(today_logs) - today_success

    # 本月签到
    month_logs = db.query(SignLog).filter(SignLog.sign_time >= month_start).all()
    month_success = sum(1 for log in month_logs if log.success)
    month_total = len(month_logs)

    # 累计奖励
    total_reward = db.query(func.sum(SignLog.reward_quota)).filter(
        SignLog.success == True
    ).scalar() or 0

    month_reward = db.query(func.sum(SignLog.reward_quota)).filter(
        SignLog.success == True,
        SignLog.sign_time >= month_start
    ).scalar() or 0

    # 签到成功率
    all_logs = db.query(SignLog).count()
    all_success = db.query(SignLog).filter(SignLog.success == True).count()
    success_rate = round(all_success / all_logs * 100, 1) if all_logs > 0 else 0

    return ApiResponse(
        success=True,
        data={
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "today_success": today_success,
            "today_fail": today_fail,
            "month_success": month_success,
            "month_total": month_total,
            "month_success_rate": round(month_success / month_total * 100, 1) if month_total > 0 else 0,
            "total_reward": total_reward,
            "total_reward_display": format_quota(total_reward),
            "month_reward": month_reward,
            "month_reward_display": format_quota(month_reward),
            "success_rate": success_rate,
        }
    )


@router.get("/daily", response_model=ApiResponse)
def get_daily_stats(
    days: int = Query(30, ge=7, le=90),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取每日签到统计（支持按日期范围或最近N天）"""
    # 如果提供了日期范围，优先使用
    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            return ApiResponse(success=False, message="日期格式错误，应为 YYYY-MM-DD")
    else:
        end = datetime.now().replace(hour=23, minute=59, second=59)
        start = (end - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0)

    # 查询每日签到数据
    logs = db.query(SignLog).filter(
        SignLog.sign_time >= start,
        SignLog.sign_time <= end
    ).all()

    # 按日期分组统计
    daily_data = {}
    current = start
    while current <= end:
        date = current.strftime("%Y-%m-%d")
        daily_data[date] = {"success": 0, "fail": 0, "reward": 0}
        current += timedelta(days=1)

    for log in logs:
        date = log.sign_time.strftime("%Y-%m-%d")
        if date in daily_data:
            if log.success:
                daily_data[date]["success"] += 1
                daily_data[date]["reward"] += log.reward_quota
            else:
                daily_data[date]["fail"] += 1

    # 转换为数组格式
    result = []
    for date in sorted(daily_data.keys()):
        data = daily_data[date]
        result.append({
            "date": date,
            "success": data["success"],
            "fail": data["fail"],
            "total": data["success"] + data["fail"],
            "reward": data["reward"],
            "reward_display": format_quota(data["reward"])
        })

    return ApiResponse(success=True, data=result)


@router.get("/monthly", response_model=ApiResponse)
def get_monthly_stats(
    months: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db)
):
    """获取月度签到统计"""
    now = datetime.now()

    result = []
    for i in range(months - 1, -1, -1):
        # 计算目标月份
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1

        month_start = datetime(year, month, 1)
        if month == 12:
            month_end = datetime(year + 1, 1, 1)
        else:
            month_end = datetime(year, month + 1, 1)

        # 查询该月数据
        month_logs = db.query(SignLog).filter(
            SignLog.sign_time >= month_start,
            SignLog.sign_time < month_end
        ).all()

        success_count = sum(1 for log in month_logs if log.success)
        fail_count = len(month_logs) - success_count
        reward = sum(log.reward_quota for log in month_logs if log.success)

        result.append({
            "month": f"{year}-{month:02d}",
            "success": success_count,
            "fail": fail_count,
            "total": len(month_logs),
            "success_rate": round(success_count / len(month_logs) * 100, 1) if month_logs else 0,
            "reward": reward,
            "reward_display": format_quota(reward)
        })

    return ApiResponse(success=True, data=result)


@router.get("/accounts", response_model=ApiResponse)
def get_account_stats(db: Session = Depends(get_db)):
    """获取各账号签到统计"""
    accounts = db.query(Account).all()

    result = []
    for account in accounts:
        # 查询该账号签到数据
        logs = db.query(SignLog).filter(SignLog.account_id == account.id).all()

        success_count = sum(1 for log in logs if log.success)
        total_reward = sum(log.reward_quota for log in logs if log.success)

        # 计算连续签到天数
        streak = calculate_streak(db, account.id)

        result.append({
            "account_id": account.id,
            "username": account.username,
            "total_signs": len(logs),
            "success_count": success_count,
            "fail_count": len(logs) - success_count,
            "success_rate": round(success_count / len(logs) * 100, 1) if logs else 0,
            "total_reward": total_reward,
            "total_reward_display": format_quota(total_reward),
            "streak_days": streak,
            "is_active": account.is_active,
            "health_status": account.health_status
        })

    # 按成功次数排序
    result.sort(key=lambda x: x["success_count"], reverse=True)

    return ApiResponse(success=True, data=result)


def calculate_streak(db: Session, account_id: int) -> int:
    """计算账号连续签到天数"""
    logs = db.query(SignLog).filter(
        SignLog.account_id == account_id,
        SignLog.success == True
    ).order_by(SignLog.sign_time.desc()).all()

    if not logs:
        return 0

    streak = 0
    today = datetime.now().date()
    current_date = today

    # 按日期分组
    signed_dates = set()
    for log in logs:
        signed_dates.add(log.sign_time.date())

    # 从今天开始往前数连续天数
    while current_date in signed_dates or (current_date == today and today not in signed_dates):
        if current_date in signed_dates:
            streak += 1
        elif current_date != today:
            break
        current_date -= timedelta(days=1)

    return streak


@router.get("/export", response_model=ApiResponse)
def export_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = Query("json", enum=["json", "csv"]),
    db: Session = Depends(get_db)
):
    """导出签到统计数据"""
    query = db.query(SignLog, Account).join(Account, Account.id == SignLog.account_id)

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(SignLog.sign_time >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(SignLog.sign_time <= end)
        except ValueError:
            pass

    logs = query.order_by(SignLog.sign_time.desc()).all()

    data = []
    for log, account in logs:
        data.append({
            "date": log.sign_time.strftime("%Y-%m-%d %H:%M:%S"),
            "account": account.username,
            "success": "成功" if log.success else "失败",
            "message": log.message,
            "reward": format_quota(log.reward_quota) if log.success else "-"
        })

    if format == "csv":
        import io
        import csv
        from fastapi.responses import StreamingResponse

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["日期", "账号", "状态", "消息", "奖励"])
        for row in data:
            writer.writerow([row["date"], row["account"], row["success"], row["message"], row["reward"]])

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=sign_stats_{datetime.now().strftime('%Y%m%d')}.csv"}
        )

    return ApiResponse(success=True, data=data)
