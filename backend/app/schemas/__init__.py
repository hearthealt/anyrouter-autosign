"""
Pydantic Schemas
"""
from .account import AccountCreate, AccountUpdate, AccountResponse, AccountInfo, LastSign, BatchImportRequest, BatchImportResultItem
from .sign import SignResult, SignLogResponse, BatchSignResult, BatchSignResponse
from .notify import (
    NotifyChannelCreate, NotifyChannelUpdate, NotifyChannelResponse,
    AccountNotifyConfig, AccountNotifyResponse, AccountNotifyUpdate
)
from .common import ApiResponse, SettingsResponse, SettingsUpdate, DashboardResponse, RecentSign, DailyTrend, LogCleanupRequest
from .auth import LoginRequest, LoginResponse, UserInfo, ChangePasswordRequest
from .platform import PlatformCreate, PlatformUpdate, PlatformResponse, PlatformBrief
from .system import VersionInfo, LatestVersionInfo, UpdateRequest, UpdateResult, UpdateStatus, SystemHealthInfo

__all__ = [
    "AccountCreate", "AccountUpdate", "AccountResponse", "AccountInfo", "LastSign",
    "BatchImportRequest", "BatchImportResultItem",
    "SignResult", "SignLogResponse", "BatchSignResult", "BatchSignResponse",
    "NotifyChannelCreate", "NotifyChannelUpdate", "NotifyChannelResponse",
    "AccountNotifyConfig", "AccountNotifyResponse", "AccountNotifyUpdate",
    "ApiResponse", "SettingsResponse", "SettingsUpdate", "DashboardResponse", "RecentSign", "DailyTrend",
    "LogCleanupRequest",
    "LoginRequest", "LoginResponse", "UserInfo", "ChangePasswordRequest",
    "PlatformCreate", "PlatformUpdate", "PlatformResponse", "PlatformBrief",
    "VersionInfo", "LatestVersionInfo", "UpdateRequest", "UpdateResult", "UpdateStatus", "SystemHealthInfo"
]
