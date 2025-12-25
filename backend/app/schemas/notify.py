"""
推送渠道相关 Schema
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class NotifyChannelCreate(BaseModel):
    """创建推送渠道请求"""
    type: str  # pushplus, wechat_mp, wechat_work, dingtalk, feishu, email
    name: str
    config: Dict[str, Any]


class NotifyChannelUpdate(BaseModel):
    """更新推送渠道请求"""
    name: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None


class NotifyChannelResponse(BaseModel):
    """推送渠道响应"""
    id: int
    type: str
    name: str
    config: Dict[str, Any]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountNotifyConfig(BaseModel):
    """账号推送配置项"""
    channel_id: int
    is_enabled: bool
    notify_config: Dict[str, Any] = {}


class AccountNotifyResponse(BaseModel):
    """账号推送配置响应"""
    channel_id: int
    channel_name: str
    channel_type: str
    is_enabled: bool
    notify_config: Dict[str, Any]


class AccountNotifyUpdate(BaseModel):
    """更新账号推送配置"""
    channels: List[AccountNotifyConfig]
