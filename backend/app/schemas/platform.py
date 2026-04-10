"""
平台相关 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PlatformCreate(BaseModel):
    """创建平台请求"""
    name: str
    base_url: str
    sign_api: str = "/api/user/sign_in"
    checkin_api: str = "/api/user/checkin"
    user_api: str = "/api/user/self"
    console_url: str = "/console"
    models_api: str = "/api/user/models"
    groups_api: str = "/api/user/self/groups"
    token_api: str = "/api/token/"
    status_api: str = "/api/status"


class PlatformUpdate(BaseModel):
    """更新平台请求"""
    name: Optional[str] = None
    base_url: Optional[str] = None
    sign_api: Optional[str] = None
    checkin_api: Optional[str] = None
    user_api: Optional[str] = None
    console_url: Optional[str] = None
    models_api: Optional[str] = None
    groups_api: Optional[str] = None
    token_api: Optional[str] = None
    status_api: Optional[str] = None


class PlatformBrief(BaseModel):
    """平台简要信息"""
    id: int
    name: str
    base_url: str

    class Config:
        from_attributes = True


class PlatformResponse(BaseModel):
    """平台响应"""
    id: int
    name: str
    base_url: str
    sign_api: str = "/api/user/sign_in"
    checkin_api: str = "/api/user/checkin"
    user_api: str = "/api/user/self"
    console_url: str = "/console"
    models_api: str = "/api/user/models"
    groups_api: str = "/api/user/self/groups"
    token_api: str = "/api/token/"
    status_api: str = "/api/status"
    is_default: bool = False
    accounts_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
