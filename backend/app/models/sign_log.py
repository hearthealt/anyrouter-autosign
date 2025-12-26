"""
签到日志模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, Text, Boolean, DateTime, BigInteger, ForeignKey

from app.database import Base


class SignLog(Base):
    """签到日志"""

    __tablename__ = "sign_logs"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    sign_time = Column(DateTime, default=datetime.now)
    success = Column(Boolean, nullable=False)
    message = Column(Text, nullable=True)
    reward_quota = Column(BigInteger, default=0)
    retry_count = Column(Integer, default=0)  # 重试次数
