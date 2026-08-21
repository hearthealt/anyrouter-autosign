"""
签到统计 API
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Account, Platform, SignLog
from app.schemas import ApiResponse
from app.utils import add_reward_total, format_quota, serialize_reward_totals

router = APIRouter(prefix="/statistics", tags=["统计"])


def _collect_reward_totals(rows) -> dict[str, int | float]:
    totals: dict[str, float] = {}
    for log, adapter_type in rows:
        if not log.success:
            continue
        add_reward_total(
            totals,
            log.reward_quota,
            log.reward_unit,
            adapter_type=adapter_type,
        )
    return serialize_reward_totals(totals)


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

    # 原有美元统计只计算 New API quota，通用 HTTP 奖励按自身单位单独聚合。
    quota_reward_query = db.query(func.sum(SignLog.reward_quota)).join(
        Account, Account.id == SignLog.account_id
    ).join(Platform, Platform.id == Account.platform_id).filter(
        SignLog.success == True,
        Platform.adapter_type == "new_api",
    )
    total_reward = quota_reward_query.scalar() or 0
    month_reward = quota_reward_query.filter(SignLog.sign_time >= month_start).scalar() or 0

    reward_rows = db.query(SignLog, Platform.adapter_type).join(
        Account, Account.id == SignLog.account_id
    ).outerjoin(Platform, Platform.id == Account.platform_id).filter(SignLog.success == True).all()
    total_reward_totals = _collect_reward_totals(reward_rows)
    month_reward_totals = _collect_reward_totals([
        row for row in reward_rows if row[0].sign_time >= month_start
    ])

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
            "total_reward_totals": total_reward_totals,
            "month_reward_totals": month_reward_totals,
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
    logs = db.query(SignLog, Platform.adapter_type).join(
        Account, Account.id == SignLog.account_id
    ).outerjoin(Platform, Platform.id == Account.platform_id).filter(
        SignLog.sign_time >= start,
        SignLog.sign_time <= end
    ).all()

    # 按日期分组统计
    daily_data = {}
    current = start
    while current <= end:
        date = current.strftime("%Y-%m-%d")
        daily_data[date] = {"success": 0, "fail": 0, "reward": 0, "reward_totals": {}}
        current += timedelta(days=1)

    for log, adapter_type in logs:
        date = log.sign_time.strftime("%Y-%m-%d")
        if date in daily_data:
            if log.success:
                daily_data[date]["success"] += 1
                if adapter_type == "new_api":
                    daily_data[date]["reward"] += log.reward_quota
                add_reward_total(
                    daily_data[date]["reward_totals"],
                    log.reward_quota,
                    log.reward_unit,
                    adapter_type=adapter_type,
                )
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
            "reward_display": format_quota(data["reward"]),
            "reward_totals": serialize_reward_totals(data["reward_totals"])
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
        month_logs = db.query(SignLog, Platform.adapter_type).join(
            Account, Account.id == SignLog.account_id
        ).outerjoin(Platform, Platform.id == Account.platform_id).filter(
            SignLog.sign_time >= month_start,
            SignLog.sign_time < month_end
        ).all()

        success_count = sum(1 for log, _ in month_logs if log.success)
        fail_count = len(month_logs) - success_count
        reward = sum(
            log.reward_quota
            for log, adapter_type in month_logs
            if log.success and adapter_type == "new_api"
        )
        reward_totals = _collect_reward_totals(month_logs)

        result.append({
            "month": f"{year}-{month:02d}",
            "success": success_count,
            "fail": fail_count,
            "total": len(month_logs),
            "success_rate": round(success_count / len(month_logs) * 100, 1) if month_logs else 0,
            "reward": reward,
            "reward_display": format_quota(reward),
            "reward_totals": reward_totals
        })

    return ApiResponse(success=True, data=result)


@router.get("/accounts", response_model=ApiResponse)
def get_account_stats(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=5, le=100),
    sort_by: str = Query("success_count", enum=["streak_days", "success_count", "success_rate", "total_reward"]),
    db: Session = Depends(get_db)
):
    """获取各账号签到统计"""
    total = db.query(func.count(Account.id)).scalar() or 0
    offset = (page - 1) * size

    success_count_expr = func.coalesce(func.sum(case((SignLog.success == True, 1), else_=0)), 0)
    total_signs_expr = func.count(SignLog.id)
    total_reward_expr = func.coalesce(func.sum(case((and_(SignLog.success == True, Platform.adapter_type == "new_api"), SignLog.reward_quota), else_=0)), 0)
    fail_count_expr = total_signs_expr - success_count_expr
    success_rate_expr = case(
        (total_signs_expr > 0, success_count_expr * 100.0 / total_signs_expr),
        else_=0.0
    )

    base_query = (
        db.query(
            Account.id.label("account_id"),
            Account.username,
            Account.is_active,
            Account.health_status,
            total_signs_expr.label("total_signs"),
            success_count_expr.label("success_count"),
            fail_count_expr.label("fail_count"),
            success_rate_expr.label("success_rate"),
            total_reward_expr.label("total_reward"),
        )
        .outerjoin(Platform, Platform.id == Account.platform_id)
        .outerjoin(SignLog, SignLog.account_id == Account.id)
        .group_by(Account.id)
    )

    if sort_by == "success_rate":
        sort_column = success_rate_expr
    elif sort_by == "total_reward":
        sort_column = total_reward_expr
    else:
        sort_column = success_count_expr

    if sort_by == "streak_days":
        rows = base_query.all()
    else:
        rows = (
            base_query
            .order_by(desc(sort_column), desc(success_count_expr), desc(success_rate_expr), desc(total_reward_expr), Account.id.asc())
            .offset(offset)
            .limit(size)
            .all()
        )

    row_account_ids = [row.account_id for row in rows]
    streaks = calculate_streaks(db, row_account_ids)
    reward_totals_by_account: dict[int, dict[str, float]] = {account_id: {} for account_id in row_account_ids}
    if row_account_ids:
        reward_rows = db.query(SignLog, Platform.adapter_type).join(
            Account, Account.id == SignLog.account_id
        ).outerjoin(Platform, Platform.id == Account.platform_id).filter(
            SignLog.account_id.in_(row_account_ids),
            SignLog.success == True,
        ).all()
        for log, adapter_type in reward_rows:
            add_reward_total(
                reward_totals_by_account.setdefault(log.account_id, {}),
                log.reward_quota,
                log.reward_unit,
                adapter_type=adapter_type,
            )

    result = []
    for row in rows:
        result.append({
            "account_id": row.account_id,
            "username": row.username,
            "total_signs": int(row.total_signs or 0),
            "success_count": int(row.success_count or 0),
            "fail_count": int(row.fail_count or 0),
            "success_rate": round(float(row.success_rate or 0), 1),
            "total_reward": int(row.total_reward or 0),
            "total_reward_display": format_quota(int(row.total_reward or 0)),
            "reward_totals": serialize_reward_totals(reward_totals_by_account.get(row.account_id, {})),
            "streak_days": streaks.get(row.account_id, 0),
            "is_active": row.is_active,
            "health_status": row.health_status
        })

    if sort_by == "streak_days":
        result.sort(
            key=lambda item: (
                item["streak_days"],
                item["success_count"],
                item["success_rate"],
                item["total_reward"],
            ),
            reverse=True
        )
        result = result[offset:offset + size]

    return ApiResponse(success=True, data={
        "items": result,
        "total": total,
        "page": page,
        "size": size
    })


def _coerce_sign_date(value):
    if hasattr(value, "date"):
        return value.date()
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _calculate_streak_from_dates(signed_dates: set) -> int:
    streak = 0
    today = datetime.now().date()
    current_date = today

    while current_date in signed_dates or (current_date == today and today not in signed_dates):
        if current_date in signed_dates:
            streak += 1
        elif current_date != today:
            break
        current_date -= timedelta(days=1)

    return streak


def calculate_streaks(db: Session, account_ids: list[int]) -> dict[int, int]:
    """批量计算账号连续签到天数。"""
    if not account_ids:
        return {}

    sign_date_expr = func.date(SignLog.sign_time)
    rows = (
        db.query(SignLog.account_id, sign_date_expr.label("sign_date"))
        .filter(
            SignLog.account_id.in_(account_ids),
            SignLog.success == True
        )
        .group_by(SignLog.account_id, sign_date_expr)
        .all()
    )

    signed_dates_by_account = {account_id: set() for account_id in account_ids}
    for account_id, sign_date in rows:
        signed_dates_by_account.setdefault(account_id, set()).add(_coerce_sign_date(sign_date))

    return {
        account_id: _calculate_streak_from_dates(signed_dates)
        for account_id, signed_dates in signed_dates_by_account.items()
    }


def calculate_streak(db: Session, account_id: int) -> int:
    """计算账号连续签到天数"""
    logs = db.query(SignLog).filter(
        SignLog.account_id == account_id,
        SignLog.success == True
    ).order_by(SignLog.sign_time.desc()).all()

    if not logs:
        return 0

    # 按日期分组
    signed_dates = set()
    for log in logs:
        signed_dates.add(log.sign_time.date())

    return _calculate_streak_from_dates(signed_dates)


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
            "reward": (log.reward_display or format_quota(log.reward_quota)) if log.success else "-"
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
