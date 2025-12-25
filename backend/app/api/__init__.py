"""
API 路由
"""
from .accounts import router as accounts_router
from .sign import router as sign_router
from .notify import router as notify_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router
from .api_endpoints import router as api_endpoints_router

__all__ = [
    "accounts_router",
    "sign_router",
    "notify_router",
    "dashboard_router",
    "settings_router",
    "api_endpoints_router"
]
