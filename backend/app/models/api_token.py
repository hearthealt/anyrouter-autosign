"""
API Token 模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ApiToken(Base):
    """API Token"""
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    token_id = Column(Integer, nullable=False, comment="AnyRouter Token ID")
    key = Column(String(100), nullable=False, comment="API Key")
    name = Column(String(100), nullable=True, comment="Token 名称")
    status = Column(Integer, default=1, comment="状态")
    remain_quota = Column(BigInteger, default=0, comment="剩余额度")
    used_quota = Column(BigInteger, default=0, comment="已用额度")
    unlimited_quota = Column(Boolean, default=False, comment="无限额度")
    model_limits_enabled = Column(Boolean, default=False, comment="模型限制启用")
    model_limits = Column(Text, nullable=True, comment="模型限制列表")
    created_time = Column(BigInteger, nullable=True, comment="创建时间戳")
    accessed_time = Column(BigInteger, nullable=True, comment="访问时间戳")
    expired_time = Column(BigInteger, default=-1, comment="过期时间戳")
    synced_at = Column(String(30), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), comment="同步时间")

    # 关联账号
    account = relationship("Account", back_populates="tokens")

    def to_dict(self):
        return {
            "id": self.id,
            "token_id": self.token_id,
            "key": self.key,
            "name": self.name,
            "status": self.status,
            "remain_quota": self.remain_quota,
            "used_quota": self.used_quota,
            "unlimited_quota": self.unlimited_quota,
            "model_limits_enabled": self.model_limits_enabled,
            "model_limits": self.model_limits,
            "created_time": self.created_time,
            "accessed_time": self.accessed_time,
            "expired_time": self.expired_time,
            "synced_at": self.synced_at
        }
