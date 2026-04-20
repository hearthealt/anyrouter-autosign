"""
API 节点模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class ApiEndpoint(Base):
    """AnyRouter API 节点（按平台隔离）"""

    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    platform_id = Column(Integer, ForeignKey("platforms.id"), nullable=False, index=True)
    endpoint_id = Column(Integer, nullable=False, comment="远程节点ID")
    route = Column(String(100), nullable=False, comment="节点名称")
    url = Column(String(255), nullable=False, comment="节点URL")
    description = Column(Text, nullable=True, comment="节点描述")
    color = Column(String(20), nullable=True, comment="状态颜色")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    platform = relationship("Platform", back_populates="api_endpoints")

    def to_dict(self):
        return {
            "id": self.id,
            "platform_id": self.platform_id,
            "endpoint_id": self.endpoint_id,
            "route": self.route,
            "url": self.url,
            "description": self.description,
            "color": self.color,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
