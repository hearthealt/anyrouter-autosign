"""
日志配置模块

功能：
- 结构化日志输出（JSON/Text）
- 日志分级（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 日志轮转（按大小 + 按时间）
- 支持接入日志分析平台（ELK/Loki）
"""
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path

from app.config import settings


class JsonFormatter(logging.Formatter):
    """JSON 格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone(timedelta(hours=8))).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段（通过 extra 参数传入）
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # 常用额外字段
        for field in ["request_id", "user_id", "username", "account_id", "ip_address"]:
            if hasattr(record, field):
                log_data[field] = getattr(record, field)

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台格式化器"""

    COLORS = {
        "DEBUG": "\033[36m",     # 青色
        "INFO": "\033[32m",      # 绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[35m",  # 紫色
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        # 添加颜色
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"

        return super().format(record)


class ContextLogger(logging.LoggerAdapter):
    """支持上下文的日志适配器"""

    def process(self, msg, kwargs):
        # 合并上下文到 extra
        extra = kwargs.get("extra", {})
        extra.update(self.extra)
        kwargs["extra"] = extra
        return msg, kwargs


def setup_logging() -> None:
    """
    初始化日志配置

    根据配置设置：
    - 控制台输出（开发环境彩色，生产环境 JSON）
    - 文件输出（JSON 格式，支持轮转）
    - 错误日志单独文件
    """
    # 获取配置
    log_level = getattr(settings, "log_level", "INFO").upper()
    log_format = getattr(settings, "log_format", "text").lower()
    log_dir = getattr(settings, "log_dir", "./logs")
    log_max_size = getattr(settings, "log_max_size", 10) * 1024 * 1024  # MB -> bytes
    log_backup_count = getattr(settings, "log_backup_count", 30)

    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))

    # 清除现有处理器
    root_logger.handlers.clear()

    # 1. 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)

    if log_format == "json":
        console_handler.setFormatter(JsonFormatter())
    else:
        # 开发模式使用彩色格式
        console_formatter = ColoredFormatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # 2. 主日志文件处理器（按大小轮转）
    main_log_file = log_path / "app.log"
    file_handler = RotatingFileHandler(
        filename=str(main_log_file),
        maxBytes=log_max_size,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)

    # 3. 错误日志文件处理器（单独记录 ERROR 及以上）
    error_log_file = log_path / "error.log"
    error_handler = RotatingFileHandler(
        filename=str(error_log_file),
        maxBytes=log_max_size,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(error_handler)

    # 4. 每日轮转日志（用于长期归档）
    daily_log_file = log_path / "app.daily.log"
    daily_handler = TimedRotatingFileHandler(
        filename=str(daily_log_file),
        when="midnight",
        interval=1,
        backupCount=log_backup_count,
        encoding="utf-8"
    )
    daily_handler.setLevel(logging.INFO)
    daily_handler.setFormatter(JsonFormatter())
    daily_handler.suffix = "%Y-%m-%d"
    root_logger.addHandler(daily_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    # 记录启动日志
    logger = logging.getLogger(__name__)
    logger.info(
        f"日志系统初始化完成",
        extra={
            "extra_data": {
                "log_level": log_level,
                "log_format": log_format,
                "log_dir": str(log_path.absolute()),
                "max_size_mb": log_max_size // (1024 * 1024),
                "backup_count": log_backup_count
            }
        }
    )


def get_logger(name: str, **context) -> ContextLogger:
    """
    获取带上下文的日志器

    Args:
        name: 日志器名称
        **context: 上下文信息（如 user_id, request_id 等）

    Returns:
        ContextLogger: 日志适配器

    Example:
        logger = get_logger(__name__, user_id=1, request_id="abc-123")
        logger.info("用户登录成功")
    """
    return ContextLogger(logging.getLogger(name), context)


# 便捷函数：记录带结构化数据的日志
def log_with_data(logger: logging.Logger, level: int, message: str, **data):
    """
    记录带结构化数据的日志

    Args:
        logger: 日志器
        level: 日志级别
        message: 日志消息
        **data: 结构化数据

    Example:
        log_with_data(logger, logging.INFO, "签到成功", account_id=1, reward=500000)
    """
    logger.log(level, message, extra={"extra_data": data})
