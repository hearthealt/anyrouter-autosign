"""
平台模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Platform(Base):
    """签到平台"""

    __tablename__ = "platforms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(255), nullable=False)

    # API 路径（各平台结构一致时使用默认值即可）
    sign_api = Column(String(255), default="/api/user/sign_in")
    checkin_api = Column(String(255), default="/api/user/checkin")
    user_api = Column(String(255), default="/api/user/self")
    console_url = Column(String(255), default="/console")
    models_api = Column(String(255), default="/api/user/models")
    groups_api = Column(String(255), default="/api/user/self/groups")
    token_api = Column(String(255), default="/api/token/")
    status_api = Column(String(255), default="/api/status")

    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    accounts = relationship("Account", back_populates="platform")
    api_endpoints = relationship("ApiEndpoint", back_populates="platform", cascade="all, delete-orphan")
