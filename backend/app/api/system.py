"""
系统信息与容器自更新 API

更新不由本进程执行，而是调用同一个 compose 里的 watchtower 侧车：
docker.sock 只挂在 watchtower 上，应用容器本身没有任何宿主机 Docker 权限。
"""
import logging

import requests
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import AuditAction, User
from app.schemas import ApiResponse, LatestVersionInfo, UpdateResult, VersionInfo
from app.services.audit import log_action
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统"])

RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_TIMEOUT = 15
# watchtower 会在更新过程中重建本容器，读超时给宽一些
WATCHTOWER_TIMEOUT = (5, 60)


def _changelog_url() -> str:
    return f"https://github.com/{settings.github_repo}/blob/{settings.update_check_ref}/CHANGELOG.md"


@router.get("/version", response_model=ApiResponse)
def get_version():
    """当前运行的版本（来自仓库根目录的 VERSION 文件）"""
    return ApiResponse(success=True, data=VersionInfo(
        name=settings.app_name,
        version=settings.app_version,
        changelog_url=_changelog_url()
    ))


@router.get("/latest-version", response_model=ApiResponse)
def get_latest_version():
    """云端最新版本

    由后端代理请求 GitHub，而不是让浏览器直连 —— 服务器通常能访问 GitHub，
    用户本地不一定能。取不到时通过 error 字段返回可读原因，不抛 5xx。
    """
    prefix = f"{RAW_BASE}/{settings.github_repo}/{settings.update_check_ref}"

    try:
        version_resp = requests.get(f"{prefix}/VERSION", timeout=GITHUB_TIMEOUT)
    except requests.RequestException as exc:
        logger.warning("检查最新版本失败: %s", exc)
        return ApiResponse(success=True, data=LatestVersionInfo(
            error=f"无法访问 GitHub：{type(exc).__name__}"
        ))

    if version_resp.status_code != 200:
        return ApiResponse(success=True, data=LatestVersionInfo(
            error=f"获取版本号失败：HTTP {version_resp.status_code}"
        ))

    # CHANGELOG 只是锦上添花，取不到不影响版本比较
    changelog = ""
    try:
        changelog_resp = requests.get(f"{prefix}/CHANGELOG.md", timeout=GITHUB_TIMEOUT)
        if changelog_resp.status_code == 200:
            changelog = changelog_resp.text
    except requests.RequestException as exc:
        logger.warning("获取 CHANGELOG 失败: %s", exc)

    return ApiResponse(success=True, data=LatestVersionInfo(
        version=version_resp.text.strip(),
        changelog=changelog
    ))


@router.post("/update", response_model=ApiResponse)
def trigger_update(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """触发容器更新

    调 watchtower 的 HTTP API，由它拉取新镜像、重建本容器并清理旧镜像。
    """
    token = (settings.watchtower_http_api_token or "").strip()
    if not token or token == "changeme":
        return ApiResponse(success=True, data=UpdateResult(
            status="error",
            message="未配置 WATCHTOWER_HTTP_API_TOKEN，请在部署目录的 .env 中设置后重启服务"
        ))

    log_action(
        db=db,
        action=AuditAction.SYSTEM_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="system",
        detail={"current_version": settings.app_version},
        request=request
    )

    endpoint = f"{settings.watchtower_url.rstrip('/')}/v1/update"

    try:
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            timeout=WATCHTOWER_TIMEOUT
        )
    except (requests.Timeout, requests.ConnectionError) as exc:
        # watchtower 在响应返回前就会把本容器干掉，连接中断恰恰说明更新已经开始。
        # 但连不上 watchtower（服务没起）也会走到这里，两种情况无法从异常上区分，
        # 因此这里按「已触发」处理，由前端轮询 /health 来确认服务是否真的回来了。
        logger.info("触发更新后连接中断（通常意味着容器正在重建）: %s", exc)
        return ApiResponse(success=True, data=UpdateResult(
            status="triggered",
            message="更新已触发，容器将在几秒内重启"
        ))
    except requests.RequestException as exc:
        logger.error("触发更新失败: %s", exc)
        return ApiResponse(success=True, data=UpdateResult(
            status="error",
            message=f"触发更新失败：{type(exc).__name__}"
        ))

    if response.status_code == 200:
        return ApiResponse(success=True, data=UpdateResult(
            status="triggered",
            message="更新已触发，容器将在几秒内重启"
        ))
    if response.status_code == 204:
        return ApiResponse(success=True, data=UpdateResult(
            status="no_update",
            message="当前已是最新镜像，无需更新"
        ))
    if response.status_code in (401, 403):
        return ApiResponse(success=True, data=UpdateResult(
            status="error",
            message="watchtower 拒绝了请求，请检查 WATCHTOWER_HTTP_API_TOKEN 两侧是否一致"
        ))

    logger.error("watchtower 返回异常状态 %s: %s", response.status_code, response.text[:200])
    return ApiResponse(success=True, data=UpdateResult(
        status="error",
        message=f"watchtower 返回 HTTP {response.status_code}"
    ))
