"""
签到相关 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SignResult(BaseModel):
    """签到结果"""
    reward_quota: int
    reward_display: str
    message: str
    sign_time: datetime
    status: str  # "success" 成功有奖励 | "already_signed" 已签到 | "failed" 失败


class SignLogResponse(BaseModel):
    """签到日志响应"""
    id: int
    account_id: int
    sign_time: datetime
    success: bool
    message: Optional[str] = None
    reward_quota: int
    reward_display: str
    retry_count: int = 0
    status: str = "failed"  # success | already_signed | failed

    class Config:
        from_attributes = True


class BatchSignResult(BaseModel):
    """批量签到单个结果"""
    account_id: int
    username: str
    success: bool
    message: str
    reward_quota: int = 0
    reward_display: str = "$0.00"
    status: str = "failed"


class BatchSignResponse(BaseModel):
    """批量签到响应"""
    total: int
    success_count: int
    fail_count: int
    already_signed_count: int
    results: List[BatchSignResult]
