"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import (
    accounts_router,
    sign_router,
    notify_router,
    dashboard_router,
    settings_router,
    api_endpoints_router,
    auth_router,
    backup_router,
    statistics_router,
    groups_router
)
from app.api.deps import get_current_user
from app.database import init_db
from app.services.scheduler import init_scheduler, shutdown_scheduler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    logger.info("正在初始化数据库...")
    init_db()
    logger.info("数据库初始化完成")

    # 启动调度器
    logger.info("正在启动定时任务调度器...")
    init_scheduler()

    logger.info(f"{settings.app_name} 启动成功")

    yield

    # 关闭时
    shutdown_scheduler()
    logger.info(f"{settings.app_name} 已关闭")


# 创建应用
app = FastAPI(
    title=settings.app_name,
    description="AnyRouter 多账号管理平台 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
# 认证路由（无需认证）
app.include_router(auth_router, prefix="/api/v1")

# 需要认证的路由
app.include_router(accounts_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(sign_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(notify_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(dashboard_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(settings_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(api_endpoints_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(backup_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(statistics_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(groups_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])


@app.get("/")
def root():
    """根路径"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}
