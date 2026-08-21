"""
应用配置

配置来源只有两处，优先级：系统环境变量 > 仓库根目录的 .env 文件 > 代码里的默认值。

Docker 部署时 .env 不会进镜像，配置由 docker-compose.yml 的 environment 注入；
本地开发和裸机部署则直接读仓库根目录的 .env。

注意：ENVIRONMENT 只能通过系统环境变量设置。它在模块导入时就要用到，
早于 pydantic 读取 .env，写在 .env 里不会生效。
"""
import os
from datetime import timezone, timedelta
from pathlib import Path
from pydantic_settings import BaseSettings

# 统一使用中国上海时区 (UTC+8)
SHANGHAI_TZ = timezone(timedelta(hours=8))


# 获取当前环境（镜像里固定为 production）
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
BASE_DIR = Path(__file__).parent.parent  # 指向 backend 目录

# 全局唯一的配置文件：仓库根目录的 .env
ENV_FILE = BASE_DIR.parent / '.env'


def _read_version() -> str:
    """读取版本号。

    仓库根目录的 VERSION 文件是唯一真源。容器内 WORKDIR 是 /app/backend，
    镜像刻意保持了同样的目录层级，所以 BASE_DIR.parent / "VERSION" 在开发和
    容器里都指向同一个文件。
    """
    for candidate in (BASE_DIR.parent / 'VERSION', BASE_DIR / 'VERSION'):
        try:
            value = candidate.read_text(encoding='utf-8').strip()
        except OSError:
            continue
        if value:
            return value
    return '0.0.0'


APP_VERSION = _read_version()


class Settings(BaseSettings):
    """应用设置"""

    # ============ 应用配置 ============
    app_name: str = "AnyRouter Admin"
    app_version: str = APP_VERSION
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
    allow_private_platform_urls: bool = False

    # ============ Web 安全配置 ============
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # ============ 配额换算 ============
    quota_to_usd_rate: int = 500000

    # ============ JWT 配置（不变配置）============
    jwt_secret_key: str = "anyrouter-admin-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 87600

    # ============ 默认管理员（环境相关）============
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"

    # ============ 前端静态文件 ============
    # 单容器部署时前端产物在 /app/web（留空即用 BASE_DIR.parent / "web"）。
    # 本地想验证同源部署可指向 ../frontend/dist。
    web_dist_dir: str = ""

    # ============ 版本检查与容器自更新 ============
    # 检查新版本时从这个仓库的 raw 地址读取 VERSION / CHANGELOG.md
    github_repo: str = "hearthealt/anyrouter-autosign"
    update_check_ref: str = "master"
    # 更新由 watchtower 侧车执行，应用容器不接触 docker.sock
    # 默认值是 compose 里的服务名，docker-compose.yml 会显式传入覆盖
    watchtower_url: str = "http://watchtower:8080"
    watchtower_http_api_token: str = ""

    class Config:
        # 仓库根目录的 .env；优先级：系统环境变量 > .env > 代码默认值
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'


# 初始化设置
settings = Settings()

# 记录当前环境
print(f"Environment: {settings.environment.upper()}")
print(f"Debug: {settings.debug}")
print(f"Log level: {settings.log_level}")
