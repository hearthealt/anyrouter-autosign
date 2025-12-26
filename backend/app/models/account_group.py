"""
账号分组模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class AccountGroup(Base):
    """账号分组"""

    __tablename__ = "account_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200), nullable=True)
    color = Column(String(20), default="default")  # default, blue, green, orange, red
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联账号
    accounts = relationship("Account", back_populates="group")
