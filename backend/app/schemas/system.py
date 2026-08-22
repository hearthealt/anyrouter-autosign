"""
系统信息与更新 Schema
"""
from typing import Optional
from pydantic import BaseModel


class VersionInfo(BaseModel):
    """当前运行的版本信息"""
    name: str
    version: str
    changelog_url: str


class LatestVersionInfo(BaseModel):
    """云端最新版本信息"""
    version: str = ""
    changelog: str = ""
    # 取不到时给出可读原因，前端直接展示
    error: Optional[str] = None


class UpdateRequest(BaseModel):
    """更新请求。update_id 由前端生成，便于请求断连后继续查询状态。"""
    update_id: Optional[str] = None


class UpdateResult(BaseModel):
    """触发更新的结果

    status:
      - triggered  已创建更新任务，前端应开始轮询健康状态
      - no_update  云端没有更新的镜像
      - error      触发失败，原因见 message
    """
    status: str
    message: str
    update_id: Optional[str] = None
    current_version: str = ""
    target_version: str = ""
    poll_interval_seconds: int = 3
    timeout_seconds: int = 180


class UpdateStatus(BaseModel):
    """更新任务与当前服务健康状态"""
    update_id: str
    status: str
    message: str
    healthy: bool = True
    ready: bool = False
    current_version: str = ""
    target_version: str = ""
    elapsed_seconds: int = 0


class SystemHealthInfo(BaseModel):
    """系统健康检查结果"""
    status: str = "ok"
    healthy: bool = True
    version: str = ""
    update_id: Optional[str] = None
    update_status: str = "idle"
    target_version: str = ""
    message: str = ""
    ready: bool = False
    elapsed_seconds: int = 0
