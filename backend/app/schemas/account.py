"""账号相关 Schema。"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.platform import PlatformBrief


class AccountCreate(BaseModel):
    """创建账号请求。"""
    session_cookie: Optional[str] = None
    user_id: Optional[str] = None
    external_user_id: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    login_username: Optional[str] = None
    login_password: Optional[str] = None
    auth_type: Optional[str] = None
    auth_data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    proxy_mode: str = "direct"
    proxy_url: Optional[str] = None
    platform_id: int
    group_id: Optional[int] = None


class AccountUpdate(BaseModel):
    """更新账号请求。"""
    session_cookie: Optional[str] = None
    user_id: Optional[str] = None
    external_user_id: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    login_username: Optional[str] = None
    login_password: Optional[str] = None
    auth_type: Optional[str] = None
    auth_data: Optional[Dict[str, Any]] = None
    clear_auth_data: Optional[bool] = None
    note: Optional[str] = None
    proxy_mode: Optional[str] = None
    proxy_url: Optional[str] = None
    clear_login_credentials: Optional[bool] = None
    is_active: Optional[bool] = None
    platform_id: Optional[int] = None
    group_id: Optional[int] = None


class NotifyChannelBrief(BaseModel):
    id: int
    type: str
    name: str


class LastSign(BaseModel):
    time: Optional[datetime] = None
    success: Optional[bool] = None
    message: Optional[str] = None


class GroupBrief(BaseModel):
    id: int
    name: str
    color: str = "default"


class AccountResponse(BaseModel):
    id: int
    username: Optional[str] = None
    display_name: Optional[str] = None
    note: Optional[str] = None
    login_username: Optional[str] = None
    has_login_credentials: bool = False
    external_user_id: Optional[str] = None
    auth_type: Optional[str] = None
    has_auth_data: bool = False
    proxy_mode: str = "direct"
    proxy_url: Optional[str] = None
    proxy_url_masked: Optional[str] = None
    anrouter_user_id: Optional[int] = None
    anyrouter_user_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    platform: Optional[PlatformBrief] = None
    notify_channels: List[NotifyChannelBrief] = Field(default_factory=list)
    last_sign: Optional[LastSign] = None
    health_status: str = "unknown"
    health_message: Optional[str] = None
    last_health_check: Optional[datetime] = None
    group_id: Optional[int] = None
    group: Optional[GroupBrief] = None
    cached_quota: int = 0
    cached_used_quota: int = 0
    quota_display: str = "$0.00"
    quota_percent: str = "0.00%"

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    account_id: int
    health_status: str
    health_message: Optional[str] = None
    checked_at: datetime


class AccountInfo(BaseModel):
    """New API 平台的实时账号信息。"""
    id: int
    username: str
    display_name: str
    role: int
    status: int
    quota: int
    used_quota: int
    request_count: int
    group: str
    aff_code: Optional[str] = None
    aff_count: int = 0
    aff_history_quota: int = 0
    quota_display: str
    used_quota_display: str
    quota_percent: str = "0.00%"
    aff_history_quota_display: str = "$0.00"
    group_id: Optional[int] = None
    local_group: Optional[GroupBrief] = None


class CreateTokenRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name: str
    remain_quota: int = 500000
    expired_time: int = -1
    unlimited_quota: bool = False
    model_limits_enabled: bool = False
    model_limits: str = ""
    allow_ips: str = ""
    group: str = "default"


class BatchImportItem(BaseModel):
    session_cookie: Optional[str] = None
    user_id: Optional[str] = None
    external_user_id: Optional[str] = None
    username: Optional[str] = None
    display_name: Optional[str] = None
    login_username: Optional[str] = None
    login_password: Optional[str] = None
    auth_type: Optional[str] = None
    auth_data: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    proxy_mode: str = "direct"
    proxy_url: Optional[str] = None
    platform_id: int
    group_id: Optional[int] = None


class BatchImportRequest(BaseModel):
    items: List[BatchImportItem]


class BatchImportResultItem(BaseModel):
    index: int
    success: bool
    message: str
    account_id: Optional[int] = None
    username: Optional[str] = None