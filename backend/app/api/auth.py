"""
认证 API
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, AuditAction
from app.schemas import (
    LoginRequest, LoginResponse, UserInfo, ChangePasswordRequest, ApiResponse
)
from app.utils import verify_password, hash_password, create_access_token
from app.api.deps import get_current_user
from app.services.audit import log_action
from app.config import settings

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=ApiResponse)
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    用户登录

    验证用户名和密码，返回 JWT Token
    """
    # 查询用户
    user = db.query(User).filter(User.username == data.username).first()

    if not user:
        # 记录登录失败日志
        log_action(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            username=data.username,
            detail={"reason": "用户不存在"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 验证密码
    if not verify_password(data.password, user.password_hash):
        # 记录登录失败日志
        log_action(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            username=user.username,
            detail={"reason": "密码错误"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查用户状态
    if not user.is_active:
        # 记录登录失败日志
        log_action(
            db=db,
            action=AuditAction.LOGIN_FAILED,
            user_id=user.id,
            username=user.username,
            detail={"reason": "用户已禁用"},
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户已被禁用"
        )

    # 创建 Token - sub 必须是字符串
    access_token = create_access_token(data={"sub": str(user.id)})

    # 记录登录成功日志
    log_action(
        db=db,
        action=AuditAction.LOGIN,
        user_id=user.id,
        username=user.username,
        request=request
    )

    return ApiResponse(
        success=True,
        message="登录成功",
        data=LoginResponse(access_token=access_token)
    )


@router.get("/me", response_model=ApiResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前用户信息
    """
    return ApiResponse(
        success=True,
        data=UserInfo(
            id=current_user.id,
            username=current_user.username,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            app_version=settings.app_version
        )
    )


@router.put("/password", response_model=ApiResponse)
def change_password(
    data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    修改密码
    """
    # 验证旧密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="原密码错误"
        )

    # 更新密码
    current_user.password_hash = hash_password(data.new_password)
    db.commit()

    # 记录密码修改日志
    log_action(
        db=db,
        action=AuditAction.PASSWORD_CHANGE,
        user_id=current_user.id,
        username=current_user.username,
        request=request
    )

    return ApiResponse(success=True, message="密码修改成功")
