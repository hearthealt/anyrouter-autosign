"""
API 节点管理
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ApiEndpoint
from app.schemas import ApiResponse
from app.services.anyrouter import anyrouter_service

router = APIRouter(prefix="/api-endpoints", tags=["API节点"])


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
    """从 AnyRouter 同步 API 节点信息"""
    success, data = anyrouter_service.get_api_status()

    if not success:
        raise HTTPException(status_code=500, detail=data.get("message", "同步失败"))

    api_info = data.get("api_info", [])
    if not api_info:
        raise HTTPException(status_code=500, detail="未获取到 API 节点信息")

    synced_count = 0
    for info in api_info:
        endpoint_id = info.get("id")
        if not endpoint_id:
            continue

        endpoint = db.query(ApiEndpoint).filter(
            ApiEndpoint.endpoint_id == endpoint_id
        ).first()

        if endpoint:
            endpoint.route = info.get("route", "")
            endpoint.url = info.get("url", "")
            endpoint.description = info.get("description", "")
            endpoint.color = info.get("color", "")
        else:
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
