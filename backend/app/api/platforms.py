"""平台管理 API。"""
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Account, Platform
from app.models.user import User
from app.schemas import ApiResponse
from app.schemas.platform import PlatformCreate, PlatformResponse, PlatformUpdate
from app.services.adapters import adapter_registry
from app.utils.platform import (
    ADAPTER_TYPE_HTTP,
    DEFAULT_CHECKIN_API,
    DEFAULT_CONSOLE_URL,
    DEFAULT_GROUPS_API,
    DEFAULT_MODELS_API,
    DEFAULT_SIGN_API,
    DEFAULT_STATUS_API,
    DEFAULT_TOKEN_API,
    DEFAULT_USER_API,
    dump_adapter_config,
    get_platform_config,
    normalize_adapter_config,
    normalize_adapter_type,
    normalize_platform_base_url,
    normalize_relative_path,
    normalize_sign_mode,
    parse_adapter_config,
    validate_public_hostname,
)

router = APIRouter(prefix="/platforms", tags=["平台管理"])


def _capabilities(adapter_type: str) -> Dict[str, bool]:
    return adapter_registry.get(adapter_type).capabilities.to_dict()


def _platform_response(db: Session, platform: Platform) -> PlatformResponse:
    adapter_type = normalize_adapter_type(platform.adapter_type)
    config = get_platform_config(platform)
    return PlatformResponse(
        id=platform.id,
        name=platform.name,
        base_url=config["base_url"],
        adapter_type=adapter_type,
        adapter_config=parse_adapter_config(platform.adapter_config),
        capabilities=_capabilities(adapter_type),
        sign_mode=config["sign_mode"],
        sign_api=config["sign_api"],
        checkin_api=config["checkin_api"],
        user_api=config["user_api"],
        console_url=config["console_url"],
        models_api=config["models_api"],
        groups_api=config["groups_api"],
        token_api=config["token_api"],
        status_api=config["status_api"],
        captcha_api=config["captcha_api"],
        is_default=bool(platform.is_default),
        accounts_count=db.query(Account).filter(Account.platform_id == platform.id).count(),
        created_at=platform.created_at,
        updated_at=platform.updated_at,
    )


def _normalize_platform_values(values: Dict[str, Any]) -> Dict[str, Any]:
    adapter_type = normalize_adapter_type(values.get("adapter_type"))
    base_url = normalize_platform_base_url(values.get("base_url"))
    validate_public_hostname(base_url, allow_private=settings.allow_private_platform_urls)
    adapter_config = normalize_adapter_config(adapter_type, values.get("adapter_config"))

    normalized = dict(values)
    normalized.update({
        "adapter_type": adapter_type,
        "adapter_config": dump_adapter_config(adapter_config),
        "base_url": base_url,
        "sign_mode": normalize_sign_mode(values.get("sign_mode")),
        "sign_api": normalize_relative_path(values.get("sign_api"), DEFAULT_SIGN_API),
        "checkin_api": normalize_relative_path(values.get("checkin_api"), DEFAULT_CHECKIN_API),
        "user_api": normalize_relative_path(values.get("user_api"), DEFAULT_USER_API),
        "console_url": normalize_relative_path(values.get("console_url"), DEFAULT_CONSOLE_URL),
        "models_api": normalize_relative_path(values.get("models_api"), DEFAULT_MODELS_API),
        "groups_api": normalize_relative_path(values.get("groups_api"), DEFAULT_GROUPS_API),
        "token_api": normalize_relative_path(values.get("token_api"), DEFAULT_TOKEN_API),
        "status_api": normalize_relative_path(values.get("status_api"), DEFAULT_STATUS_API),
        "captcha_api": normalize_relative_path(values.get("captcha_api"), "", optional=True),
    })
    if adapter_type == ADAPTER_TYPE_HTTP:
        # HTTP 适配器真正的签到路径位于 adapter_config.request.path。
        normalized["sign_mode"] = "api"
    return normalized


@router.get("", response_model=ApiResponse)
def get_platforms(
    page: Optional[int] = None,
    size: Optional[int] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Platform)
    cleaned_keyword = (keyword or "").strip()
    if cleaned_keyword:
        like_pattern = f"%{cleaned_keyword}%"
        query = query.filter(or_(Platform.name.ilike(like_pattern), Platform.base_url.ilike(like_pattern)))

    total = query.count()
    resolved_page = max(page or 1, 1)
    resolved_size = min(max(size or 10, 1), 100)
    platforms_query = query.order_by(Platform.created_at.desc(), Platform.id.desc())
    if page is not None or size is not None or cleaned_keyword:
        platforms_query = platforms_query.offset((resolved_page - 1) * resolved_size).limit(resolved_size)
    result = [_platform_response(db, platform) for platform in platforms_query.all()]

    if page is None and size is None and not cleaned_keyword:
        return ApiResponse(success=True, data=result)
    return ApiResponse(success=True, data={
        "items": result,
        "total": total,
        "page": resolved_page,
        "size": resolved_size,
    })


@router.post("", response_model=ApiResponse)
def create_platform(
    data: PlatformCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="平台名称不能为空")
    if db.query(Platform).filter(Platform.name == name).first():
        raise HTTPException(status_code=400, detail="平台名称已存在")

    try:
        values = _normalize_platform_values(data.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    has_default = db.query(Platform.id).filter(Platform.is_default == True).first() is not None
    platform = Platform(
        name=name,
        is_default=not has_default,
        **{key: values[key] for key in (
            "base_url", "adapter_type", "adapter_config", "sign_mode", "sign_api",
            "checkin_api", "user_api", "console_url", "models_api", "groups_api",
            "token_api", "status_api", "captcha_api",
        )},
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)
    return ApiResponse(success=True, message="平台创建成功", data=_platform_response(db, platform))


@router.get("/{platform_id}", response_model=ApiResponse)
def get_platform(platform_id: int, db: Session = Depends(get_db)):
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")
    return ApiResponse(success=True, data=_platform_response(db, platform))


@router.put("/{platform_id}", response_model=ApiResponse)
def update_platform(
    platform_id: int,
    data: PlatformUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")

    updates = data.model_dump(exclude_unset=True)
    if "name" in updates:
        name = str(updates["name"] or "").strip()
        if not name:
            raise HTTPException(status_code=400, detail="平台名称不能为空")
        existing = db.query(Platform).filter(Platform.name == name, Platform.id != platform_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="平台名称已存在")
        platform.name = name

    current = {
        "base_url": platform.base_url,
        "adapter_type": platform.adapter_type,
        "adapter_config": parse_adapter_config(platform.adapter_config),
        "sign_mode": platform.sign_mode,
        "sign_api": platform.sign_api,
        "checkin_api": platform.checkin_api,
        "user_api": platform.user_api,
        "console_url": platform.console_url,
        "models_api": platform.models_api,
        "groups_api": platform.groups_api,
        "token_api": platform.token_api,
        "status_api": platform.status_api,
        "captcha_api": platform.captcha_api,
    }
    current.update({key: value for key, value in updates.items() if key != "name"})
    try:
        values = _normalize_platform_values(current)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    for key in (
        "base_url", "adapter_type", "adapter_config", "sign_mode", "sign_api",
        "checkin_api", "user_api", "console_url", "models_api", "groups_api",
        "token_api", "status_api", "captcha_api",
    ):
        setattr(platform, key, values[key])

    db.commit()
    db.refresh(platform)
    return ApiResponse(success=True, message="平台更新成功", data=_platform_response(db, platform))


@router.delete("/{platform_id}", response_model=ApiResponse)
def delete_platform(
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    del current_user
    platform = db.query(Platform).filter(Platform.id == platform_id).first()
    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")

    accounts_count = db.query(Account).filter(Account.platform_id == platform_id).count()
    if accounts_count > 0:
        raise HTTPException(status_code=400, detail=f"该平台下有 {accounts_count} 个账号，请先迁移或删除这些账号")

    was_default = platform.is_default
    db.delete(platform)
    db.commit()
    if was_default:
        next_platform = db.query(Platform).order_by(Platform.created_at.asc()).first()
        if next_platform:
            next_platform.is_default = True
            db.commit()
    return ApiResponse(success=True, message="平台删除成功")