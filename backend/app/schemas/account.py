"""
账号相关 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class AccountCreate(BaseModel):
    """创建账号请求"""
    session_cookie: str
    user_id: str  # new-api-user，必填


class AccountUpdate(BaseModel):
    """更新账号请求"""
    session_cookie: Optional[str] = None
    user_id: Optional[str] = None  # new-api-user
    is_active: Optional[bool] = None


class NotifyChannelBrief(BaseModel):
    """推送渠道简要信息"""
    id: int
    type: str
    name: str


class LastSign(BaseModel):
    """最后签到信息"""
    time: Optional[datetime] = None
    success: Optional[bool] = None
    message: Optional[str] = None


class AccountResponse(BaseModel):
    """账号响应"""
    id: int
    username: Optional[str] = None
    display_name: Optional[str] = None
    anyrouter_user_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    notify_channels: List[NotifyChannelBrief] = []
    last_sign: Optional[LastSign] = None

    class Config:
        from_attributes = True


class AccountInfo(BaseModel):
    """账号实时信息（从 AnyRouter 获取）"""
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
    aff_history_quota: int = 0  # 推广所得额度
    quota_display: str
    used_quota_display: str
    aff_history_quota_display: str = "$0.00"  # 推广所得显示
