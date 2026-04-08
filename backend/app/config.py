"""
应用配置
支持多环境：development（本地开发）、production（生产）
自动加载 .env 文件，优先级：系统环境变量 > .env.{ENVIRONMENT} > .env

配置分类：
- 环境相关：DEBUG、LOG_LEVEL、LOG_FORMAT、LOG_DIR 等（随环境变化）
- 不变配置：AnyRouter API、JWT、请求配置 等（所有环境相同）
"""
import os
from datetime import timezone, timedelta
from pathlib import Path
from pydantic_settings import BaseSettings

# 统一使用中国上海时区 (UTC+8)
SHANGHAI_TZ = timezone(timedelta(hours=8))


# 获取当前环境
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
BASE_DIR = Path(__file__).parent.parent  # 指向 backend 目录

# 根据环境选择加载的 .env 文件
# 开发环境优先加载 .env.local，生产环境加载 .env.production
if ENVIRONMENT == 'development':
    ENV_FILE = BASE_DIR / '.env.local'
else:
    ENV_FILE = BASE_DIR / '.env.production'


class Settings(BaseSettings):
    """应用设置"""

    # ============ 应用配置 ============
    app_name: str = "AnyRouter Admin"
    app_version: str = "1.1.0"
    debug: bool = False  # 默认关闭，由 .env 文件覆盖
    environment: str = ENVIRONMENT  # 使用当前环境变量值

    # ============ 数据库配置 ============
    database_url: str = "sqlite:///./data/anyrouter.db"

    # ============ 日志配置（环境相关）============
    log_level: str = "INFO"           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "text"          # text（开发）或 json（生产）
    log_dir: str = "./logs"           # 日志目录
    log_max_size: int = 10            # 单文件最大大小（MB）
    log_backup_count: int = 30        # 保留文件数量

    # ============ AnyRouter API（不变配置）============
    anyrouter_base_url: str = "https://anyrouter.top"
    anyrouter_user_api: str = "/api/user/self"
    anyrouter_sign_api: str = "/api/user/sign_in"
    anyrouter_console_url: str = "/console"
    anyrouter_models_api: str = "/api/user/models"
    anyrouter_groups_api: str = "/api/user/self/groups"
    anyrouter_token_api: str = "/api/token/"
    anyrouter_status_api: str = "/api/status"
    anyrouter_proxy_enabled: bool = False
    anyrouter_proxy_url: str = ""

    # ============ 反爬虫配置 ============
    anti_crawler_mask: str = "3000176000856006061501533003690027800375"
    anti_crawler_pos_list: list = [
        15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27,
        22, 23, 25, 13, 6, 11, 39, 18, 20, 8, 14, 21, 32, 26,
        2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36
    ]

    # ============ 请求配置（不变配置）============
    request_timeout: int = 30
    retry_times: int = 3
    retry_interval: int = 3

    # ============ 配额换算 ============
    quota_to_usd_rate: int = 500000

    # ============ JWT 配置（不变配置）============
    jwt_secret_key: str = "anyrouter-admin-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 87600

    # ============ 默认管理员（环境相关）============
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"

    class Config:
        # 动态加载 .env 文件
        # 开发环境：优先加载 .env.local，然后 .env
        # 生产环境：加载 .env.production，然后 .env
        # 优先级：系统环境变量 > 指定的 .env 文件 > .env > 默认值
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'


# 初始化设置
settings = Settings()

# 记录当前环境
print(ENVIRONMENT)
print(f"🌍 应用环境: {settings.environment.upper()}")
print(f"🔧 调试模式: {settings.debug}")
print(f"📝 日志级别: {settings.log_level}")
