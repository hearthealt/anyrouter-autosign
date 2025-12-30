"""
系统日志 API
"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.config import settings
from app.schemas import ApiResponse

router = APIRouter(prefix="/logs", tags=["系统日志"])


def get_log_dir() -> Path:
    """获取日志目录"""
    log_dir = Path(settings.log_dir)
    if not log_dir.is_absolute():
        # 相对于 backend 目录
        log_dir = Path(__file__).parent.parent.parent / settings.log_dir
    return log_dir


@router.get("/files", response_model=ApiResponse)
def get_log_files():
    """获取日志文件列表"""
    log_dir = get_log_dir()

    if not log_dir.exists():
        return ApiResponse(success=True, data=[])

    files = []
    for f in log_dir.iterdir():
        if f.is_file() and f.suffix == ".log" or ".log." in f.name:
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


def format_size(size: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
