"""
推送服务基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class NotifyBase(ABC):
    """推送服务基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        """
        发送通知

        Args:
            title: 标题
            content: 内容
            account_config: 账号专属配置

        Returns:
            bool: 是否发送成功
        """
        pass

    @abstractmethod
    def test(self) -> bool:
        """
        测试推送

        Returns:
            bool: 是否测试成功
        """
        pass


class NotifyFactory:
    """推送服务工厂"""

    _notifiers = {}

    @classmethod
    def register(cls, channel_type: str):
        """注册推送服务"""
        def decorator(notifier_class):
            cls._notifiers[channel_type] = notifier_class
            return notifier_class
        return decorator

    @classmethod
    def create(cls, channel_type: str, config: Dict[str, Any]) -> NotifyBase:
        """创建推送服务实例"""
        notifier_class = cls._notifiers.get(channel_type)
        if not notifier_class:
            raise ValueError(f"未知的推送渠道类型: {channel_type}")
        return notifier_class(config)

    @classmethod
    def get_supported_types(cls):
        """获取支持的推送类型"""
        return list(cls._notifiers.keys())
