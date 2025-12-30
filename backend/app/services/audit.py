"""
审计日志服务
"""
import json
from typing import Optional, Any
from sqlalchemy.orm import Session
from fastapi import Request

from app.models.audit_log import AuditLog


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP"""
    # 优先从 X-Forwarded-For 获取（反向代理场景）
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # 其次从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后从连接获取
    if request.client:
        return request.client.host

    return "unknown"


def log_action(
    db: Session,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[int] = None,
    target_name: Optional[str] = None,
    detail: Optional[Any] = None,
    request: Optional[Request] = None
):
    """
    记录审计日志

    Args:
        db: 数据库会话
        action: 操作类型（使用 AuditAction 常量）
        user_id: 操作用户ID
        username: 操作用户名
        target_type: 目标类型（account/setting/channel/group等）
        target_id: 目标ID
        target_name: 目标名称
        detail: 详细信息（会被转为JSON）
        request: FastAPI 请求对象（用于获取IP和UA）
    """
    # 处理详细信息
    detail_json = None
    if detail is not None:
        if isinstance(detail, str):
            detail_json = detail
        else:
            try:
                detail_json = json.dumps(detail, ensure_ascii=False)
            except (TypeError, ValueError):
                detail_json = str(detail)

    # 获取IP和UA
    ip_address = None
    user_agent = None
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")[:500]  # 截断过长的UA

    # 创建日志记录
    audit_log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        target_type=target_type,
        target_id=target_id,
        target_name=target_name,
        detail=detail_json,
        ip_address=ip_address,
        user_agent=user_agent
    )

    db.add(audit_log)
    db.commit()

    return audit_log
