"""
系统信息与容器自更新 API

更新不由本进程执行，而是调用同一个 compose 里的 watchtower 侧车：
docker.sock 只挂在 watchtower 上，应用容器本身没有任何宿主机 Docker 权限。
"""
import logging
import re

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

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TIMEOUT = 15
# watchtower 会在更新过程中重建本容器，读超时给宽一些
WATCHTOWER_TIMEOUT = (5, 60)


def _changelog_url() -> str:
    return f"https://github.com/{settings.github_repo}/releases/latest"


_VERSION_PATTERN = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def _version_parts(value: str) -> tuple[int, int, int] | None:
    match = _VERSION_PATTERN.match(str(value or "").strip())
    if not match:
        return None
    return tuple(map(int, match.groups()))


def _is_newer_version(latest: str, current: str) -> bool:
    latest_parts = _version_parts(latest)
    current_parts = _version_parts(current)
    return bool(latest_parts and current_parts and latest_parts > current_parts)


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
    # releases/latest 只会返回已经创建成功的正式 Release。发布工作流中 Release
    # 又依赖 Docker 镜像任务，因此镜像构建或推送失败时，这里不会提前暴露新版本。
    endpoint = f"{GITHUB_API_BASE}/repos/{settings.github_repo}/releases/latest"

    try:
        release_resp = requests.get(
            endpoint,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": f"anyrouter-autosign/{settings.app_version}",
            },
            timeout=GITHUB_TIMEOUT,
        )
    except requests.RequestException as exc:
        logger.warning("检查最新发布版本失败: %s", exc)
        return ApiResponse(success=True, data=LatestVersionInfo(
            error=f"无法访问 GitHub：{type(exc).__name__}"
        ))

    if release_resp.status_code == 404:
        return ApiResponse(success=True, data=LatestVersionInfo(
            error="GitHub 上还没有可用的正式发布版本"
        ))
    if release_resp.status_code != 200:
        return ApiResponse(success=True, data=LatestVersionInfo(
            error=f"获取最新发布版本失败：HTTP {release_resp.status_code}"
        ))

    try:
        release = release_resp.json()
    except ValueError as exc:
        logger.warning("解析 GitHub Release 响应失败: %s", exc)
        return ApiResponse(success=True, data=LatestVersionInfo(
            error="GitHub 返回的发布信息格式无效"
        ))

    if not isinstance(release, dict):
        return ApiResponse(success=True, data=LatestVersionInfo(
            error="GitHub 返回的发布信息格式无效"
        ))

    version = str(release.get("tag_name") or "").strip()
    if not version:
        return ApiResponse(success=True, data=LatestVersionInfo(
            error="GitHub 最新发布缺少版本标签"
        ))

    changelog = release.get("body")
    if not isinstance(changelog, str):
        changelog = ""

    return ApiResponse(success=True, data=LatestVersionInfo(
        version=version,
        changelog=changelog.strip()
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

    # 后端再次以正式 Release 为准，不能只依赖前端按钮状态。
    latest = get_latest_version().data
    if latest.error:
        return ApiResponse(success=True, data=UpdateResult(
            status="error",
            message=f"无法确认可更新版本：{latest.error}"
        ))
    if not _version_parts(latest.version) or not _version_parts(settings.app_version):
        return ApiResponse(success=True, data=UpdateResult(
            status="error",
            message="当前版本或最新发布版本的格式无效"
        ))
    if not _is_newer_version(latest.version, settings.app_version):
        return ApiResponse(success=True, data=UpdateResult(
            status="no_update",
            message="当前已是最新正式发布版本，无需更新"
        ))

    log_action(
        db=db,
        action=AuditAction.SYSTEM_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="system",
        detail={
            "current_version": settings.app_version,
            "target_version": latest.version,
        },
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
