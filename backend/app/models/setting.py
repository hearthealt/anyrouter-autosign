"""
系统设置模型
"""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime

from app.database import Base


class Setting(Base):
    """系统设置"""

    __tablename__ = "settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
