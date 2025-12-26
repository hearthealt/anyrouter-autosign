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
    group_id: Optional[int] = None


class AccountUpdate(BaseModel):
    """更新账号请求"""
    session_cookie: Optional[str] = None
    user_id: Optional[str] = None  # new-api-user
    is_active: Optional[bool] = None
    group_id: Optional[int] = None


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


class GroupBrief(BaseModel):
    """分组简要信息"""
    id: int
    name: str
    color: str = "default"


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
    # 健康状态
    health_status: str = "unknown"  # healthy, unhealthy, unknown
    health_message: Optional[str] = None
    last_health_check: Optional[datetime] = None
    # 分组
    group_id: Optional[int] = None
    group: Optional[GroupBrief] = None
    # 缓存的额度信息
    cached_quota: int = 0
    cached_used_quota: int = 0
    quota_display: str = "$0.00"
    quota_percent: str = "0.00%"

    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    account_id: int
    health_status: str
    health_message: Optional[str] = None
    checked_at: datetime


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
    group: str  # 远程用户组
    aff_code: Optional[str] = None
    aff_count: int = 0
    aff_history_quota: int = 0  # 推广所得额度
    quota_display: str
    used_quota_display: str
    quota_percent: str = "0.00%"  # 剩余额度百分比
    aff_history_quota_display: str = "$0.00"  # 推广所得显示
    # 本地分组
    group_id: Optional[int] = None
    local_group: Optional[GroupBrief] = None


class CreateTokenRequest(BaseModel):
    """创建令牌请求"""
    name: str
    remain_quota: int = 500000
    expired_time: int = -1  # -1 表示永不过期
    unlimited_quota: bool = False
    model_limits_enabled: bool = False
    model_limits: str = ""  # 逗号分隔的模型列表
    allow_ips: str = ""
    group: str = "default"
