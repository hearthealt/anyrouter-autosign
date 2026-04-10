"""
兼容旧导入路径
"""
from .anrouter import AnyRouterService, anrouter_service

anyrouter_service = anrouter_service

__all__ = ["AnyRouterService", "anrouter_service", "anyrouter_service"]
