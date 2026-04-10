"""
业务服务
"""
from .anrouter import anrouter_service, AnyRouterService
from .notify import NotifyFactory, NotifyBase

anyrouter_service = anrouter_service

__all__ = ["anrouter_service", "anyrouter_service", "AnyRouterService", "NotifyFactory", "NotifyBase"]
