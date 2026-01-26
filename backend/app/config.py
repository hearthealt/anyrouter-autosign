"""
应用配置
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # 应用配置
    app_name: str = "AnyRouter Admin"
    app_version: str = "1.1.0"
    debug: bool = True

    # 数据库配置
    database_url: str = "sqlite:///./data/anyrouter.db"

    # 日志配置
    log_level: str = "INFO"           # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "json"          # text（开发）或 json（生产）
    log_dir: str = "/www/wwwroot/anyrouter/backend/logs"           # 日志目录
    log_max_size: int = 10            # 单文件最大大小（MB）
    log_backup_count: int = 30        # 保留文件数量

    # AnyRouter API
    anyrouter_base_url: str = "https://anyrouter.top"
    anyrouter_user_api: str = "/api/user/self"
    anyrouter_sign_api: str = "/api/user/sign_in"
    anyrouter_console_url: str = "/console"
    anyrouter_models_api: str = "/api/user/models"
    anyrouter_groups_api: str = "/api/user/self/groups"
    anyrouter_token_api: str = "/api/token/"
    anyrouter_status_api: str = "/api/status"

    # 反爬虫配置
    anti_crawler_mask: str = "3000176000856006061501533003690027800375"
    anti_crawler_pos_list: list = [
        15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27,
        22, 23, 25, 13, 6, 11, 39, 18, 20, 8, 14, 21, 32, 26,
        2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36
    ]

    # 请求配置
    request_timeout: int = 300
    retry_times: int = 3
    retry_interval: int = 3

    # 配额换算 (1 USD = 500000 quota)
    quota_to_usd_rate: int = 500000

    # JWT 配置
    jwt_secret_key: str = "anyrouter-admin-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 87600

    # 默认管理员
    default_admin_username: str = "admin"
    default_admin_password: str = "zaq1,lp-"

    class Config:
        env_file = ".env"


settings = Settings()
