"""
系统日志 API
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import User
from app.models.audit_log import AuditAction
from app.schemas import ApiResponse, LogCleanupRequest
from app.services.audit import log_action
from app.services.log_cleanup import cleanup_log_files, format_size, get_log_dir, is_log_file
from app.api.deps import get_current_user

router = APIRouter(prefix="/logs", tags=["系统日志"])


@router.get("/files", response_model=ApiResponse)
def get_log_files():
    """获取日志文件列表"""
    log_dir = get_log_dir()

    if not log_dir.exists():
        return ApiResponse(success=True, data=[])

    files = []
    for f in log_dir.iterdir():
        if is_log_file(f):
            stat = f.stat()
            files.append({
                "name": f.name,
                "size": stat.st_size,
                "size_display": format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })

    # 按修改时间倒序
    files.sort(key=lambda x: x["modified"], reverse=True)

    return ApiResponse(success=True, data=files)


@router.get("", response_model=ApiResponse)
def get_logs(
    file: str = Query("app.log", description="日志文件名"),
    level: Optional[str] = Query(None, description="日志级别筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    lines: int = Query(200, ge=10, le=2000, description="返回行数"),
    offset: int = Query(0, ge=0, description="偏移行数")
):
    """
    获取日志内容

    - 支持按级别筛选
    - 支持关键词搜索
    - 支持分页（通过 lines 和 offset）
    """
    log_dir = get_log_dir()
    log_file = log_dir / file

    # 安全检查：防止路径遍历
    try:
        log_file = log_file.resolve()
        if not str(log_file).startswith(str(log_dir.resolve())):
            raise HTTPException(status_code=400, detail="无效的文件名")
    except Exception:
        raise HTTPException(status_code=400, detail="无效的文件名")

    if not log_file.exists():
        return ApiResponse(success=True, data={"logs": [], "total": 0, "has_more": False})

    try:
        # 读取文件（从尾部读取，最新的在前）
        all_lines = read_file_tail(log_file, max_lines=5000)

        # 解析日志行
        parsed_logs = []
        for line in all_lines:
            log_entry = parse_log_line(line)
            if log_entry:
                # 级别筛选
                if level and log_entry.get("level", "").upper() != level.upper():
                    continue
                # 关键词搜索
                if keyword and keyword.lower() not in line.lower():
                    continue
                parsed_logs.append(log_entry)

        total = len(parsed_logs)

        # 分页
        paginated = parsed_logs[offset:offset + lines]

        return ApiResponse(success=True, data={
            "logs": paginated,
            "total": total,
            "has_more": offset + lines < total
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {str(e)}")


@router.get("/download/{filename}")
def download_log(filename: str):
    """下载日志文件"""
    log_dir = get_log_dir()
    log_file = log_dir / filename

    # 安全检查
    try:
        log_file = log_file.resolve()
        if not str(log_file).startswith(str(log_dir.resolve())):
            raise HTTPException(status_code=400, detail="无效的文件名")
    except Exception:
        raise HTTPException(status_code=400, detail="无效的文件名")

    if not log_file.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(log_file),
        filename=filename,
        media_type="text/plain"
    )


@router.post("/cleanup", response_model=ApiResponse)
def cleanup_logs(
    data: LogCleanupRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    批量清理日志文件

    before_days 为空或 0 表示清理全部归档并把活跃文件截空；
    否则只删除该天数之前的归档文件，活跃文件不动。
    """
    before_days = data.before_days
    result = cleanup_log_files(before_days)
    freed_display = format_size(result["freed_bytes"])

    log_action(
        db=db,
        action=AuditAction.SYSTEM_LOG_CLEAR,
        user_id=current_user.id,
        username=current_user.username,
        target_type="system_log",
        detail={"before_days": before_days, **result},
        request=request
    )

    scope = f"{before_days} 天前" if before_days else "全部"
    return ApiResponse(
        success=True,
        message=f"已清理{scope}日志，删除 {result['removed_files']} 个归档，释放 {freed_display}",
        data={**result, "freed_display": freed_display}
    )


@router.delete("/{filename}", response_model=ApiResponse)
def clear_log(filename: str):
    """清空日志文件"""
    log_dir = get_log_dir()
    log_file = log_dir / filename

    # 安全检查
    try:
        log_file = log_file.resolve()
        if not str(log_file).startswith(str(log_dir.resolve())):
            raise HTTPException(status_code=400, detail="无效的文件名")
    except Exception:
        raise HTTPException(status_code=400, detail="无效的文件名")

    if not log_file.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 清空文件内容（不删除文件）
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")
        return ApiResponse(success=True, message="日志已清空")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")


def read_file_tail(filepath: Path, max_lines: int = 1000) -> List[str]:
    """从文件尾部读取指定行数"""
    lines = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            # 使用 deque 或者直接读取（小文件）
            all_lines = f.readlines()
            # 取最后 max_lines 行，并反转（最新的在前）
            lines = all_lines[-max_lines:][::-1]
    except Exception:
        pass
    return lines


def parse_log_line(line: str) -> Optional[dict]:
    """解析日志行"""
    line = line.strip()
    if not line:
        return None

    # 尝试解析 JSON 格式
    if line.startswith("{"):
        try:
            data = json.loads(line)
            return {
                "timestamp": data.get("timestamp", ""),
                "level": data.get("level", "INFO"),
                "logger": data.get("logger", ""),
                "message": data.get("message", ""),
                "raw": line,
                "is_json": True,
                "extra": {k: v for k, v in data.items()
                         if k not in ["timestamp", "level", "logger", "message", "module", "function", "line"]}
            }
        except json.JSONDecodeError:
            pass

    # 解析文本格式: 2025-12-30 10:15:30 [INFO] app.main - message
    import re
    pattern = r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\S+)\s+-\s+(.+)"
    match = re.match(pattern, line)
    if match:
        return {
            "timestamp": match.group(1),
            "level": match.group(2),
            "logger": match.group(3),
            "message": match.group(4),
            "raw": line,
            "is_json": False,
            "extra": {}
        }

    # 无法解析，返回原始内容
    return {
        "timestamp": "",
        "level": "INFO",
        "logger": "",
        "message": line,
        "raw": line,
        "is_json": False,
        "extra": {}
    }
