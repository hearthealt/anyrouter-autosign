"""
通用响应和设置 Schema
"""
from typing import Optional, Any, List
from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    """统一 API 响应"""
    success: bool
    message: str = ""
    data: Optional[Any] = None


class SettingsResponse(BaseModel):
    """系统设置响应"""
    auto_sign_enabled: bool = False
    auto_sign_time: str = "08:00"
    health_check_enabled: bool = True
    health_check_interval: int = 6
    sign_retry_enabled: bool = True
    sign_max_retries: int = 3
    sign_retry_interval: int = 30
    sign_notify_enabled: bool = False
    sign_notify_channel_ids: List[int] = Field(default_factory=list)
    quota_warning_threshold: float = 5.0
    audit_log_retention_days: int = 0
    system_log_retention_days: int = 0


class SettingsUpdate(BaseModel):
    """更新系统设置"""
    auto_sign_enabled: Optional[bool] = None
    auto_sign_time: Optional[str] = None
    health_check_enabled: Optional[bool] = None
    health_check_interval: Optional[int] = None
    sign_retry_enabled: Optional[bool] = None
    sign_max_retries: Optional[int] = None
    sign_retry_interval: Optional[int] = None
    sign_notify_enabled: Optional[bool] = None
    sign_notify_channel_ids: Optional[List[int]] = None
    quota_warning_threshold: Optional[float] = None
    audit_log_retention_days: Optional[int] = None
    system_log_retention_days: Optional[int] = None


class LogCleanupRequest(BaseModel):
    """日志清理请求。before_days 为 None 或 0 表示全部清理。"""
    before_days: Optional[int] = Field(default=None, ge=0, le=365)


class RecentSign(BaseModel):
    """最近签到"""
    username: str
    sign_time: str
    success: bool


class DailyTrend(BaseModel):
    """每日签到趋势"""
    date: str
    success: int
    fail: int
    reward: int = 0
    reward_display: str = "$0.00"
    reward_totals: dict[str, int | float] = Field(default_factory=dict)


class DashboardResponse(BaseModel):
    """仪表盘数据"""
    account_count: int
    active_account_count: int
    normal_account_count: int = 0
    unhealthy_account_count: int = 0
    disabled_account_count: int = 0
    today_sign_count: int
    today_sign_success: int
    total_quota: int
    total_used_quota: int
    total_quota_display: str
    total_used_quota_display: str
    total_request_count: int
    month_reward: int = 0
    month_reward_display: str = "$0.00"
    month_reward_totals: dict[str, int | float] = Field(default_factory=dict)
    success_rate: float = 0
    recent_signs: List[RecentSign]
    daily_trend: List[DailyTrend] = []
