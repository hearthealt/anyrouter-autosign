"""
API 节点模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class ApiEndpoint(Base):
    """AnyRouter API 节点"""

    __tablename__ = "api_endpoints"

    id = Column(Integer, primary_key=True, index=True)
    endpoint_id = Column(Integer, nullable=False, unique=True, comment="远程节点ID")
    route = Column(String(100), nullable=False, comment="节点名称")
    url = Column(String(255), nullable=False, comment="节点URL")
    description = Column(Text, nullable=True, comment="节点描述")
    color = Column(String(20), nullable=True, comment="状态颜色")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "endpoint_id": self.endpoint_id,
            "route": self.route,
            "url": self.url,
            "description": self.description,
            "color": self.color,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
