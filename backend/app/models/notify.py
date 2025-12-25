"""
推送渠道模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey

from app.database import Base


class NotifyChannel(Base):
    """推送渠道"""

    __tablename__ = "notify_channels"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # pushplus, wechat_mp, wechat_work, dingtalk, feishu, email
    name = Column(String(100), nullable=False)
    config = Column(Text, nullable=False)  # JSON 格式的配置
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class AccountNotify(Base):
    """账号推送关联"""

    __tablename__ = "account_notify"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("notify_channels.id"), nullable=False)
    notify_config = Column(Text, nullable=True)  # JSON 格式的账号专属配置
    is_enabled = Column(Boolean, default=True)
