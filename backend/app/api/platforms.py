"""
平台管理 API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Platform, Account
from app.schemas import ApiResponse
from app.schemas.platform import PlatformCreate, PlatformUpdate, PlatformResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.utils.platform import normalize_sign_mode

router = APIRouter(prefix="/platforms", tags=["平台管理"])


@router.get("", response_model=ApiResponse)
def get_platforms(db: Session = Depends(get_db)):
    """获取平台列表"""
    platforms = db.query(Platform).order_by(Platform.created_at.desc()).all()

    result = []
    for p in platforms:
        accounts_count = db.query(Account).filter(Account.platform_id == p.id).count()
        result.append(PlatformResponse(
            id=p.id,
            name=p.name,
            base_url=p.base_url,
            sign_mode=p.sign_mode or "api",
            sign_api=p.sign_api,
            checkin_api=p.checkin_api,
            user_api=p.user_api,
            console_url=p.console_url,
            models_api=p.models_api,
            groups_api=p.groups_api,
            token_api=p.token_api,
            status_api=p.status_api,
            is_default=p.is_default,
            accounts_count=accounts_count,
            created_at=p.created_at,
            updated_at=p.updated_at
        ))

    return ApiResponse(success=True, data=result)


@router.post("", response_model=ApiResponse)
def create_platform(
    data: PlatformCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建平台"""
    # 检查名称是否重复
    existing = db.query(Platform).filter(Platform.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="平台名称已存在")

    has_default_platform = db.query(Platform.id).filter(Platform.is_default == True).first() is not None

    platform = Platform(
        name=data.name,
        base_url=data.base_url,
        sign_mode=normalize_sign_mode(data.sign_mode),
        sign_api=data.sign_api,
        checkin_api=data.checkin_api,
        user_api=data.user_api,
        console_url=data.console_url,
        models_api=data.models_api,
        groups_api=data.groups_api,
        token_api=data.token_api,
        status_api=data.status_api,
        is_default=not has_default_platform
    )

    db.add(platform)
    db.commit()
    db.refresh(platform)

    return ApiResponse(
        success=True,
        message="平台创建成功",
        data=PlatformResponse(
            id=platform.id,
            name=platform.name,
            base_url=platform.base_url,
            sign_mode=platform.sign_mode or "api",
            sign_api=platform.sign_api,
            checkin_api=platform.checkin_api,
            user_api=platform.user_api,
            console_url=platform.console_url,
            models_api=platform.models_api,
            groups_api=platform.groups_api,
            token_api=platform.token_api,
            status_api=platform.status_api,
            is_default=platform.is_default,
            accounts_count=0,
            created_at=platform.created_at,
            updated_at=platform.updated_at
        )
    )


@router.get("/{platform_id}", response_model=ApiResponse)
def get_platform(platform_id: int, db: Session = Depends(get_db)):
    """获取平台详情"""
    platform = db.query(Platform).filter(Platform.id == platform_id).first()

    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")

    accounts_count = db.query(Account).filter(Account.platform_id == platform.id).count()

    return ApiResponse(
        success=True,
        data=PlatformResponse(
            id=platform.id,
            name=platform.name,
            base_url=platform.base_url,
            sign_mode=platform.sign_mode or "api",
            sign_api=platform.sign_api,
            checkin_api=platform.checkin_api,
            user_api=platform.user_api,
            console_url=platform.console_url,
            models_api=platform.models_api,
            groups_api=platform.groups_api,
            token_api=platform.token_api,
            status_api=platform.status_api,
            is_default=platform.is_default,
            accounts_count=accounts_count,
            created_at=platform.created_at,
            updated_at=platform.updated_at
        )
    )


@router.put("/{platform_id}", response_model=ApiResponse)
def update_platform(
    platform_id: int,
    data: PlatformUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新平台"""
    platform = db.query(Platform).filter(Platform.id == platform_id).first()

    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")

    if data.name is not None:
        # 检查名称是否与其他平台重复
        existing = db.query(Platform).filter(
            Platform.name == data.name,
            Platform.id != platform_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="平台名称已存在")
        platform.name = data.name

    if data.base_url is not None:
        platform.base_url = data.base_url
    if data.sign_mode is not None:
        platform.sign_mode = normalize_sign_mode(data.sign_mode)
    if data.sign_api is not None:
        platform.sign_api = data.sign_api
    if data.checkin_api is not None:
        platform.checkin_api = data.checkin_api
    if data.user_api is not None:
        platform.user_api = data.user_api
    if data.console_url is not None:
        platform.console_url = data.console_url
    if data.models_api is not None:
        platform.models_api = data.models_api
    if data.groups_api is not None:
        platform.groups_api = data.groups_api
    if data.token_api is not None:
        platform.token_api = data.token_api
    if data.status_api is not None:
        platform.status_api = data.status_api

    db.commit()
    db.refresh(platform)

    return ApiResponse(success=True, message="平台更新成功")


@router.delete("/{platform_id}", response_model=ApiResponse)
def delete_platform(
    platform_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除平台"""
    platform = db.query(Platform).filter(Platform.id == platform_id).first()

    if not platform:
        raise HTTPException(status_code=404, detail="平台不存在")

    # 检查是否有关联账号
    accounts_count = db.query(Account).filter(Account.platform_id == platform_id).count()
    if accounts_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该平台下有 {accounts_count} 个账号，请先迁移或删除这些账号"
        )

    was_default = platform.is_default
    db.delete(platform)
    db.commit()

    if was_default:
        next_platform = db.query(Platform).order_by(Platform.created_at.asc()).first()
        if next_platform:
            next_platform.is_default = True
            db.commit()

    return ApiResponse(success=True, message="平台删除成功")
