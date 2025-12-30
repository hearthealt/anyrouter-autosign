"""
审计日志模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from app.database import Base


class AuditLog(Base):
    """审计日志"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 操作用户
    username = Column(String(50), nullable=True)  # 用户名（冗余存储，方便查询）
    action = Column(String(50), nullable=False, index=True)  # 操作类型
    target_type = Column(String(50), nullable=True)  # 目标类型(account/setting/channel等)
    target_id = Column(Integer, nullable=True)  # 目标ID
    target_name = Column(String(100), nullable=True)  # 目标名称
    detail = Column(Text, nullable=True)  # 详细信息(JSON)
    ip_address = Column(String(50), nullable=True)  # 操作IP
    user_agent = Column(String(500), nullable=True)  # 浏览器UA
    created_at = Column(DateTime, default=datetime.now, index=True)


# 操作类型常量
class AuditAction:
    """审计操作类型"""
    # 认证相关
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"

    # 账号相关
    ACCOUNT_CREATE = "account_create"
    ACCOUNT_UPDATE = "account_update"
    ACCOUNT_DELETE = "account_delete"

    # 设置相关
    SETTING_UPDATE = "setting_update"

    # 推送渠道相关
    CHANNEL_CREATE = "channel_create"
    CHANNEL_UPDATE = "channel_update"
    CHANNEL_DELETE = "channel_delete"

    # 备份相关
    BACKUP_EXPORT = "backup_export"
    BACKUP_IMPORT = "backup_import"

    # 令牌相关
    TOKEN_CREATE = "token_create"
    TOKEN_UPDATE = "token_update"
    TOKEN_DELETE = "token_delete"

    # 分组相关
    GROUP_CREATE = "group_create"
    GROUP_UPDATE = "group_update"
    GROUP_DELETE = "group_delete"


# 操作类型显示名称
ACTION_NAMES = {
    AuditAction.LOGIN: "登录",
    AuditAction.LOGIN_FAILED: "登录失败",
    AuditAction.LOGOUT: "登出",
    AuditAction.PASSWORD_CHANGE: "修改密码",
    AuditAction.ACCOUNT_CREATE: "创建账号",
    AuditAction.ACCOUNT_UPDATE: "更新账号",
    AuditAction.ACCOUNT_DELETE: "删除账号",
    AuditAction.SETTING_UPDATE: "更新设置",
    AuditAction.CHANNEL_CREATE: "创建推送渠道",
    AuditAction.CHANNEL_UPDATE: "更新推送渠道",
    AuditAction.CHANNEL_DELETE: "删除推送渠道",
    AuditAction.BACKUP_EXPORT: "导出备份",
    AuditAction.BACKUP_IMPORT: "导入备份",
    AuditAction.TOKEN_CREATE: "创建令牌",
    AuditAction.TOKEN_UPDATE: "更新令牌",
    AuditAction.TOKEN_DELETE: "删除令牌",
    AuditAction.GROUP_CREATE: "创建分组",
    AuditAction.GROUP_UPDATE: "更新分组",
    AuditAction.GROUP_DELETE: "删除分组",
}
