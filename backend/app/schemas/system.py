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


class UpdateResult(BaseModel):
    """触发更新的结果

    status:
      - triggered  已触发，容器即将重启
      - no_update  云端没有更新的镜像
      - error      触发失败，原因见 message
    """
    status: str
    message: str
