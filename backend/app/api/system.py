"""
系统信息与容器自更新 API

更新不由本进程执行，而是调用同一个 compose 里的 watchtower 侧车：
docker.sock 只挂在 watchtower 上，应用容器本身没有任何宿主机 Docker 权限。
"""
import json
import logging
import re
import threading
import time
import uuid

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, Query, Request
from sqlalchemy.orm import Session

from app.config import BASE_DIR, settings
from app.database import get_db
from app.models import AuditAction, User
from app.schemas import (
    ApiResponse,
    LatestVersionInfo,
    SystemHealthInfo,
    UpdateRequest,
    UpdateResult,
    UpdateStatus,
    VersionInfo,
)
from app.services.audit import log_action
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system", tags=["系统"])

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TIMEOUT = 15
# watchtower 会在更新过程中重建本容器，读超时给宽一些
WATCHTOWER_TIMEOUT = (5, 60)
# 给反向代理留出时间接收已返回的成功响应，再触发容器重建。
WATCHTOWER_TRIGGER_DELAY = 1
UPDATE_POLL_INTERVAL_SECONDS = 3
UPDATE_TIMEOUT_SECONDS = 180

# 更新标记必须放在 Docker 的 data 挂载卷中，应用容器重建后仍可读取。
# 本地开发时对应 backend/data/update-state.json。
UPDATE_STATE_FILE = BASE_DIR / "data" / "update-state.json"
_UPDATE_STATE_LOCK = threading.Lock()


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


def _version_at_least(current: str, target: str) -> bool:
    current_parts = _version_parts(current)
    target_parts = _version_parts(target)
    return bool(current_parts and target_parts and current_parts >= target_parts)


def _read_update_state() -> dict | None:
    """读取跨容器保留的更新状态；文件损坏时按无状态处理。"""
    try:
        payload = json.loads(UPDATE_STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_update_state(state: dict) -> None:
    """原子写入更新状态，避免进程重启时留下半截 JSON。"""
    UPDATE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = UPDATE_STATE_FILE.with_name(
        f".{UPDATE_STATE_FILE.name}.{uuid.uuid4().hex}.tmp"
    )
    temp_file.write_text(
        json.dumps(state, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    temp_file.replace(UPDATE_STATE_FILE)


def _save_update_state(state: dict) -> None:
    with _UPDATE_STATE_LOCK:
        _write_update_state(state)


def _create_update_state(update_id: str, target_version: str) -> dict:
    state = {
        "update_id": update_id,
        "status": "triggered",
        "message": "更新任务已创建，正在等待 Watchtower 执行",
        "source_version": settings.app_version,
        "target_version": target_version,
        "started_at": time.time(),
    }
    _save_update_state(state)
    return state


def _update_state(update_id: str, status: str, message: str) -> None:
    with _UPDATE_STATE_LOCK:
        state = _read_update_state()
        if not state or state.get("update_id") != update_id:
            return
        state["status"] = status
        state["message"] = message
        state["updated_at"] = time.time()
        _write_update_state(state)


def _state_elapsed(state: dict | None) -> int:
    if not state:
        return 0
    try:
        return max(0, int(time.time() - float(state.get("started_at", time.time()))))
    except (TypeError, ValueError):
        return 0


def _status_for_update(update_id: str) -> UpdateStatus:
    """根据持久化任务和当前运行版本生成状态。"""
    state = _read_update_state()
    current_version = settings.app_version

    if not state or state.get("update_id") != update_id:
        return UpdateStatus(
            update_id=update_id,
            status="unknown",
            message="正在确认更新任务状态",
            healthy=True,
            ready=False,
            current_version=current_version,
        )

    target_version = str(state.get("target_version") or "")
    elapsed = _state_elapsed(state)

    # 新容器启动后，版本号是最可靠的完成信号。即使旧容器在触发请求时
    # 连接被 Cloudflare 中断，只要新版本已经运行，就直接判定 ready。
    if _version_at_least(current_version, target_version):
        if state.get("status") != "ready":
            _update_state(update_id, "ready", "新版本服务已恢复")
        return UpdateStatus(
            update_id=update_id,
            status="ready",
            message="新版本服务已恢复",
            healthy=True,
            ready=True,
            current_version=current_version,
            target_version=target_version,
            elapsed_seconds=elapsed,
        )

    state_status = str(state.get("status") or "triggered")
    return UpdateStatus(
        update_id=update_id,
        status=state_status,
        message=str(state.get("message") or "正在更新服务，请稍候"),
        healthy=True,
        ready=False,
        current_version=current_version,
        target_version=target_version,
        elapsed_seconds=elapsed,
    )


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


@router.get("/health", response_model=ApiResponse)
def get_system_health(
    update_id: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    """供更新流程轮询的健康检查。

    该接口能确认当前容器已经可以处理请求，并同时返回当前运行版本。
    更新期间传入 update_id 时，还会根据跨容器持久化状态返回 ready。
    """
    status = _status_for_update(update_id) if update_id else None
    return ApiResponse(success=True, data=SystemHealthInfo(
        status="ok",
        healthy=True,
        version=settings.app_version,
        update_id=update_id,
        update_status=status.status if status else "idle",
        target_version=status.target_version if status else "",
        message=status.message if status else "服务运行正常",
        ready=status.ready if status else True,
        elapsed_seconds=status.elapsed_seconds if status else 0,
    ))


@router.get("/update-status", response_model=ApiResponse)
def get_update_status(
    update_id: str = Query(..., min_length=1, max_length=128),
    current_user: User = Depends(get_current_user),
):
    """读取跨容器保留的更新状态和当前版本。"""
    return ApiResponse(success=True, data=_status_for_update(update_id))


def _request_watchtower_update(endpoint: str, token: str, update_id: str) -> None:
    """在更新接口响应发送完成后，后台通知 watchtower 开始重建容器。"""
    time.sleep(WATCHTOWER_TRIGGER_DELAY)

    try:
        response = requests.get(
            endpoint,
            headers={"Authorization": f"Bearer {token}"},
            timeout=WATCHTOWER_TIMEOUT
        )
    except requests.RequestException as exc:
        # 应用容器可能在这里已经开始被 watchtower 重建；异常只写日志，
        # 保留 triggered 状态，让新容器根据版本号判定 ready。
        logger.info("后台触发 watchtower 更新时连接中断: %s", exc)
        _update_state(update_id, "triggered", "更新连接中断，正在确认新容器状态")
        return

    if response.status_code == 200:
        logger.info("watchtower 已接受更新请求")
        _update_state(update_id, "updating", "Watchtower 已接受更新，正在拉取镜像并重启服务")
    elif response.status_code == 204:
        logger.info("watchtower 未发现需要更新的镜像")
        _update_state(update_id, "no_update", "Watchtower 未发现可更新的镜像")
    elif response.status_code in (401, 403):
        logger.error("watchtower 拒绝更新请求，HTTP %s", response.status_code)
        _update_state(update_id, "failed", "Watchtower 鉴权失败，请检查更新配置")
    else:
        logger.error("watchtower 返回异常状态 %s: %s", response.status_code, response.text[:200])
        _update_state(update_id, "failed", f"Watchtower 返回异常状态 HTTP {response.status_code}")


@router.post("/update", response_model=ApiResponse)
def trigger_update(
    request: Request,
    background_tasks: BackgroundTasks,
    payload: UpdateRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建更新任务并异步触发 Watchtower。

    接口不再人为阻塞 15-30 秒。先把任务标记写入 data 挂载卷，再返回
    update_id；前端随后通过 /system/health 轮询新版本是否真正恢复。
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

    requested_update_id = (payload.update_id if payload else None) or ""
    update_id = requested_update_id.strip()
    if not update_id or len(update_id) > 128 or not re.fullmatch(r"[A-Za-z0-9_-]+", update_id):
        update_id = uuid.uuid4().hex

    log_action(
        db=db,
        action=AuditAction.SYSTEM_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="system",
        detail={
            "update_id": update_id,
            "current_version": settings.app_version,
            "target_version": latest.version,
        },
        request=request
    )

    _create_update_state(update_id, latest.version)
    endpoint = f"{settings.watchtower_url.rstrip('/')}/v1/update"

    # BackgroundTasks 会在当前响应已经发送给浏览器之后执行，避免重建当前
    # 容器时产生 502。真正是否完成不看这个触发请求，而看版本健康轮询。
    background_tasks.add_task(_request_watchtower_update, endpoint, token, update_id)

    return ApiResponse(success=True, data=UpdateResult(
        status="triggered",
        message="更新任务已创建，正在启动更新流程",
        update_id=update_id,
        current_version=settings.app_version,
        target_version=latest.version,
        poll_interval_seconds=UPDATE_POLL_INTERVAL_SECONDS,
        timeout_seconds=UPDATE_TIMEOUT_SECONDS,
    ))
