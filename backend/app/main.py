"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings, BASE_DIR
from app.core.logging import setup_logging
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
    groups_router,
    audit_router,
    logs_router,
    platforms_router,
    events_router,
    system_router
)
from app.api.deps import get_current_user
from app.database import init_db
from app.services.scheduler import init_scheduler, shutdown_scheduler

# 初始化日志系统
setup_logging()

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
    description="多平台签到管理 API",
    version=settings.app_version,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
app.include_router(audit_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(logs_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(platforms_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(system_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(events_router, prefix="/api/v1")


@app.get("/health")
def health():
    """健康检查"""
    return {"status": "ok"}


# ---------- 前端静态文件 ----------
# 单容器部署时前端构建产物在 /app/web（镜像里 WORKDIR 是 /app/backend）。
# 本地开发没有这个目录，前端走 Vite dev server，这里整段跳过。
WEB_DIST = Path(settings.web_dist_dir) if settings.web_dist_dir else BASE_DIR.parent / "web"

if WEB_DIST.is_dir():
    assets_dir = WEB_DIST / "assets"
    if assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    index_file = WEB_DIST / "index.html"

    # 必须放在所有路由注册之后：FastAPI 按注册顺序匹配，
    # 否则这个兜底会把 /api/v1/*、/docs、/health 全吃掉。
    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):
        """SPA 兜底：静态文件直接返回，其余路径交给前端路由。"""
        # 未命中的 API 路径要返回 404，不能喂 index.html
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        if full_path:
            candidate = (WEB_DIST / full_path).resolve()
            # 防目录穿越：只允许 WEB_DIST 内的文件
            if candidate.is_file() and candidate.is_relative_to(WEB_DIST.resolve()):
                return FileResponse(candidate)

        return FileResponse(index_file)

else:
    # 没有前端产物（本地开发、裸机部署由 nginx 提供静态文件）时保留原来的根路径信息
    @app.get("/")
    def root():
        """根路径"""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs"
        }
