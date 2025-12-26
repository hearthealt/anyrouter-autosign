"""
通用响应和设置 Schema
"""
from typing import Optional, Any, List
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应"""
    success: bool
    message: str = ""
    data: Optional[Any] = None


class SettingsResponse(BaseModel):
    """系统设置响应"""
    auto_sign_enabled: bool = False
    auto_sign_time: str = "08:00"
    sign_retry_times: int = 3
    sign_retry_interval: int = 5


class SettingsUpdate(BaseModel):
    """更新系统设置"""
    auto_sign_enabled: Optional[bool] = None
    auto_sign_time: Optional[str] = None
    sign_retry_times: Optional[int] = None
    sign_retry_interval: Optional[int] = None


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


class DashboardResponse(BaseModel):
    """仪表盘数据"""
    account_count: int
    active_account_count: int
    unhealthy_account_count: int = 0
    today_sign_count: int
    today_sign_success: int
    total_quota: int
    total_used_quota: int
    total_quota_display: str
    total_used_quota_display: str
    total_request_count: int
    month_reward: int = 0
    month_reward_display: str = "$0.00"
    success_rate: float = 0
    recent_signs: List[RecentSign]
    daily_trend: List[DailyTrend] = []
