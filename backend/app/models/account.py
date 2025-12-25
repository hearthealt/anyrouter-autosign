"""
账号模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
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

    # 关联 tokens
    tokens = relationship("ApiToken", back_populates="account", cascade="all, delete-orphan")
