"""
账号模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Account(Base):
    """AnyRouter 账号"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    session_cookie = Column(Text, nullable=False)
    anyrouter_user_id = Column(Integer, nullable=True)
    username = Column(String(100), nullable=True)
    display_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 健康状态
    health_status = Column(String(20), default="unknown")  # healthy, unhealthy, unknown
    health_message = Column(String(255), nullable=True)
    last_health_check = Column(DateTime, nullable=True)

    # 分组
    group_id = Column(Integer, ForeignKey("account_groups.id"), nullable=True)
    group = relationship("AccountGroup", back_populates="accounts")

    # 配额缓存 (在签到、健康检查、刷新信息时更新)
    cached_quota = Column(Integer, default=0)
    cached_used_quota = Column(Integer, default=0)
    cached_request_count = Column(Integer, default=0)
    cached_user_group = Column(String(50), nullable=True)  # 用户组
    cached_aff_code = Column(String(50), nullable=True)    # 推广码
    cached_aff_count = Column(Integer, default=0)          # 推广人数
    cached_aff_history_quota = Column(Integer, default=0)  # 推广所得
    quota_updated_at = Column(DateTime, nullable=True)

    # 关联 tokens
    tokens = relationship("ApiToken", back_populates="account", cascade="all, delete-orphan")
