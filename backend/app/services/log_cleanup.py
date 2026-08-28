"""
日志清理服务

手动清理（API）和定时保留策略（scheduler）共用这里的逻辑，
避免两条入口的判定规则漂移。
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# 与 app/core/logging.py 里三个 handler 的 filename 一一对应。
# 这些文件被 handler 持有句柄，只能清空内容、不能删除 ——
# 删掉后 handler 仍写向已被移除的 inode，日志会静默丢失。
ACTIVE_LOG_FILES = {"app.log", "error.log", "app.daily.log"}


def get_log_dir() -> Path:
    """获取日志目录"""
    log_dir = Path(settings.log_dir)
    if not log_dir.is_absolute():
        # 相对于 backend 目录
        log_dir = Path(__file__).parent.parent.parent / settings.log_dir
    return log_dir


def format_size(size: int) -> str:
    """格式化文件大小"""
    value = float(size)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def is_log_file(path: Path) -> bool:
    """判断是否为日志文件（含轮转归档，如 app.log.1 / app.daily.log.2026-08-26）"""
    return path.is_file() and (path.suffix == ".log" or ".log." in path.name)


def iter_archived_logs(log_dir: Optional[Path] = None):
    """遍历归档日志文件（排除三个活跃文件）"""
    log_dir = log_dir or get_log_dir()
    if not log_dir.exists():
        return
    for path in log_dir.iterdir():
        if path.name in ACTIVE_LOG_FILES:
            continue
        if is_log_file(path):
            yield path


def cleanup_audit_logs(db: Session, before_days: Optional[int] = None) -> int:
    """
    清理审计日志记录。

    Args:
        db: 数据库会话
        before_days: 保留最近多少天；None 或 0 表示全部删除

    Returns:
        删除的记录条数
    """
    query = db.query(AuditLog)

    if before_days:
        cutoff = datetime.now() - timedelta(days=before_days)
        query = query.filter(AuditLog.created_at < cutoff)

    deleted = query.delete(synchronize_session=False)
    db.commit()

    return deleted


def cleanup_log_files(before_days: Optional[int] = None) -> dict:
    """
    清理日志文件。

    归档文件按修改时间删除；全部清理时额外把三个活跃文件截断为空
    （不删文件本身，见 ACTIVE_LOG_FILES 说明）。

    Args:
        before_days: 保留最近多少天；None 或 0 表示全部清理

    Returns:
        {"removed_files": int, "freed_bytes": int, "truncated": int}
    """
    log_dir = get_log_dir()
    cutoff = datetime.now() - timedelta(days=before_days) if before_days else None

    removed_files = 0
    freed_bytes = 0
    truncated = 0

    for path in iter_archived_logs(log_dir):
        try:
            stat = path.stat()
            if cutoff and datetime.fromtimestamp(stat.st_mtime) >= cutoff:
                continue
            size = stat.st_size
            path.unlink()
            removed_files += 1
            freed_bytes += size
        except OSError as e:
            logger.warning(f"删除日志归档失败 {path.name}: {e}")

    # 全部清理时才截断活跃文件；按天保留不动它们（当天的日志还在写）
    if not before_days:
        for name in ACTIVE_LOG_FILES:
            path = log_dir / name
            if not path.exists():
                continue
            try:
                freed_bytes += path.stat().st_size
                with open(path, "w", encoding="utf-8"):
                    pass
                truncated += 1
            except OSError as e:
                logger.warning(f"清空日志文件失败 {name}: {e}")

    return {
        "removed_files": removed_files,
        "freed_bytes": freed_bytes,
        "truncated": truncated,
    }
