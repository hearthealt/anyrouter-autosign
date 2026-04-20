"""
API 节点管理
"""
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiEndpoint, Platform
from app.schemas import ApiResponse
from app.services import anrouter_service
from app.utils import get_platform_config

router = APIRouter(prefix="/api-endpoints", tags=["API节点"])


def get_default_platform(db: Session) -> Optional[Platform]:
    """获取默认平台。"""
    return db.query(Platform).filter(Platform.is_default == True).first()


def resolve_platforms(db: Session, platform_id: Optional[int]) -> List[Platform]:
    """按 platform_id 解析目标平台列表，未指定则返回全部平台。"""
    if platform_id is not None:
        platform = db.query(Platform).filter(Platform.id == platform_id).first()
        if not platform:
            raise HTTPException(status_code=404, detail="平台不存在")
        return [platform]
    return db.query(Platform).order_by(Platform.is_default.desc(), Platform.id).all()


def build_fallback_endpoint(platform: Platform) -> Dict[str, Any]:
    """当平台 /api/status 未返回 api_info 时，用 base_url 造一条兜底节点。"""
    return {
        "id": platform.id,
        "route": platform.name or "默认节点",
        "url": platform.base_url,
        "description": "平台未返回 api_info，使用 Base URL 作为默认节点",
        "color": "green",
    }


def sync_platform_endpoints(db: Session, platform: Platform) -> Tuple[int, Optional[str]]:
    """同步单个平台的 API 节点。返回 (同步数量, 错误信息)。"""
    platform_config = get_platform_config(platform)
    success, data = anrouter_service.get_api_status(
        platform_config["base_url"],
        status_api=platform_config["status_api"],
        console_url=platform_config["console_url"],
    )

    api_info: List[Dict[str, Any]] = []
    if success and isinstance(data, dict):
        raw_api_info = data.get("api_info", [])
        if isinstance(raw_api_info, list):
            api_info = [item for item in raw_api_info if isinstance(item, dict)]

    if not api_info:
        # 接口失败或返回为空都回退到 base_url
        api_info = [build_fallback_endpoint(platform)]

    db.query(ApiEndpoint).filter(ApiEndpoint.platform_id == platform.id).delete()

    synced_count = 0
    for info in api_info:
        endpoint_id = info.get("id")
        if endpoint_id is None:
            continue
        endpoint = ApiEndpoint(
            platform_id=platform.id,
            endpoint_id=endpoint_id,
            route=info.get("route", "") or "",
            url=info.get("url", "") or platform.base_url,
            description=info.get("description", "") or "",
            color=info.get("color", "") or "",
        )
        db.add(endpoint)
        synced_count += 1

    db.commit()

    error_message = None
    if not success:
        error_message = data.get("message") if isinstance(data, dict) else "同步失败"
    return synced_count, error_message


@router.get("", response_model=ApiResponse)
def get_endpoints(
    platform_id: Optional[int] = Query(None, description="按平台过滤"),
    db: Session = Depends(get_db),
):
    """获取 API 节点，可按平台过滤。"""
    query = db.query(ApiEndpoint)
    if platform_id is not None:
        query = query.filter(ApiEndpoint.platform_id == platform_id)
    endpoints = query.order_by(ApiEndpoint.platform_id, ApiEndpoint.endpoint_id).all()
    return ApiResponse(
        success=True,
        data=[ep.to_dict() for ep in endpoints],
    )


@router.post("/sync", response_model=ApiResponse)
def sync_endpoints(
    platform_id: Optional[int] = Query(None, description="仅同步指定平台，不填则同步全部"),
    db: Session = Depends(get_db),
):
    """从平台同步 API 节点信息。"""
    platforms = resolve_platforms(db, platform_id)
    if not platforms:
        raise HTTPException(status_code=400, detail="请先创建至少一个平台")

    total_synced = 0
    partial_errors: List[str] = []
    for platform in platforms:
        synced, error = sync_platform_endpoints(db, platform)
        total_synced += synced
        if error:
            partial_errors.append(f"{platform.name}: {error}")

    if len(platforms) == 1 and partial_errors and total_synced == 0:
        raise HTTPException(status_code=500, detail=partial_errors[0])

    message = f"同步成功，共 {total_synced} 个节点"
    if partial_errors:
        message += f"；部分平台使用 Base URL 兜底（{'; '.join(partial_errors)}）"

    return ApiResponse(
        success=True,
        message=message,
        data={"count": total_synced, "platform_count": len(platforms)},
    )
