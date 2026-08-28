"""
审计日志 API
"""
import io
import csv
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog, AuditAction, ACTION_NAMES
from app.models import User
from app.schemas import ApiResponse, LogCleanupRequest
from app.services.audit import log_action
from app.services.log_cleanup import cleanup_audit_logs
from app.api.deps import get_current_user

router = APIRouter(prefix="/audit", tags=["审计日志"])


@router.get("/logs", response_model=ApiResponse)
def get_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    查询审计日志

    支持按操作类型、目标类型、时间范围、关键词筛选
    """
    query = db.query(AuditLog)

    # 操作类型筛选
    if action:
        query = query.filter(AuditLog.action == action)

    # 目标类型筛选
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    # 时间范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= end)
        except ValueError:
            pass

    # 关键词搜索（用户名、目标名称、详情）
    if keyword:
        keyword_filter = f"%{keyword}%"
        query = query.filter(
            or_(
                AuditLog.username.ilike(keyword_filter),
                AuditLog.target_name.ilike(keyword_filter),
                AuditLog.detail.ilike(keyword_filter),
                AuditLog.ip_address.ilike(keyword_filter)
            )
        )

    # 统计总数
    total = query.count()

    # 分页查询
    logs = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * size).limit(size).all()

    # 格式化结果
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "user_id": log.user_id,
            "username": log.username or "-",
            "action": log.action,
            "action_name": ACTION_NAMES.get(log.action, log.action),
            "target_type": log.target_type,
            "target_id": log.target_id,
            "target_name": log.target_name or "-",
            "detail": log.detail,
            "ip_address": log.ip_address or "-",
            "user_agent": log.user_agent,
            "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None
        })

    return ApiResponse(
        success=True,
        data={
            "items": result,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )


@router.get("/actions", response_model=ApiResponse)
def get_action_types():
    """获取所有操作类型"""
    actions = [
        {"value": action, "label": name}
        for action, name in ACTION_NAMES.items()
    ]
    return ApiResponse(success=True, data=actions)


@router.post("/cleanup", response_model=ApiResponse)
def cleanup_logs(
    data: LogCleanupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    清理审计日志

    before_days 为空或 0 表示清空全部；否则只删除该天数之前的记录。
    """
    before_days = data.before_days
    deleted = cleanup_audit_logs(db, before_days)

    # 这条记录写在删除之后，因此不会被本次清理带走 —— 留下操作痕迹
    log_action(
        db=db,
        action=AuditAction.AUDIT_LOG_CLEAR,
        user_id=current_user.id,
        username=current_user.username,
        target_type="audit_log",
        detail={"before_days": before_days, "deleted": deleted},
        request=request
    )

    scope = f"{before_days} 天前" if before_days else "全部"
    return ApiResponse(
        success=True,
        message=f"已清理{scope}审计日志，共 {deleted} 条",
        data={"deleted": deleted}
    )


@router.get("/export")
def export_audit_logs(
    action: Optional[str] = None,
    target_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    format: str = Query("csv", enum=["csv", "json"]),
    db: Session = Depends(get_db)
):
    """
    导出审计日志

    支持 CSV 和 JSON 格式
    """
    query = db.query(AuditLog)

    # 操作类型筛选
    if action:
        query = query.filter(AuditLog.action == action)

    # 目标类型筛选
    if target_type:
        query = query.filter(AuditLog.target_type == target_type)

    # 时间范围筛选
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= end)
        except ValueError:
            pass

    # 限制导出数量
    logs = query.order_by(AuditLog.created_at.desc()).limit(10000).all()

    if format == "json":
        import json
        data = []
        for log in logs:
            data.append({
                "id": log.id,
                "username": log.username,
                "action": log.action,
                "action_name": ACTION_NAMES.get(log.action, log.action),
                "target_type": log.target_type,
                "target_name": log.target_name,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None
            })

        content = json.dumps(data, ensure_ascii=False, indent=2)
        return StreamingResponse(
            io.BytesIO(content.encode('utf-8')),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.json"
            }
        )
    else:
        # CSV 格式
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["时间", "用户", "操作", "目标类型", "目标名称", "详情", "IP地址"])

        for log in logs:
            writer.writerow([
                log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
                log.username or "",
                ACTION_NAMES.get(log.action, log.action),
                log.target_type or "",
                log.target_name or "",
                log.detail or "",
                log.ip_address or ""
            ])

        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=audit_logs_{datetime.now().strftime('%Y%m%d')}.csv"
            }
        )
