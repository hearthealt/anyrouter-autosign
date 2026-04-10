"""
API 节点管理
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
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


@router.get("", response_model=ApiResponse)
def get_endpoints(db: Session = Depends(get_db)):
    """获取所有 API 节点"""
    endpoints = db.query(ApiEndpoint).order_by(ApiEndpoint.endpoint_id).all()
    return ApiResponse(
        success=True,
        data=[ep.to_dict() for ep in endpoints]
    )


@router.post("/sync", response_model=ApiResponse)
def sync_endpoints(db: Session = Depends(get_db)):
    """从平台同步 API 节点信息"""
    default_platform = get_default_platform(db)
    if not default_platform:
        raise HTTPException(status_code=400, detail="请先创建并保留一个默认平台")

    platform_config = get_platform_config(default_platform)
    success, data = anrouter_service.get_api_status(
        platform_config["base_url"],
        status_api=platform_config["status_api"],
        console_url=platform_config["console_url"]
    )

    if not success:
        raise HTTPException(status_code=500, detail=data.get("message", "同步失败"))

    api_info = data.get("api_info", [])
    if not isinstance(api_info, list):
        api_info = []

    # 先删除所有旧节点
    db.query(ApiEndpoint).delete()

    # 添加新节点
    synced_count = 0
    for info in api_info:
        endpoint_id = info.get("id")
        if not endpoint_id:
            continue

        endpoint = ApiEndpoint(
            endpoint_id=endpoint_id,
            route=info.get("route", ""),
            url=info.get("url", ""),
            description=info.get("description", ""),
            color=info.get("color", "")
        )
        db.add(endpoint)
        synced_count += 1

    db.commit()

    return ApiResponse(
        success=True,
        message=f"同步成功，共 {synced_count} 个节点",
        data={"count": synced_count}
    )
