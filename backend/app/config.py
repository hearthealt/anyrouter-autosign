"""
应用配置
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用设置"""

    # 应用配置
    app_name: str = "AnyRouter Admin"
    debug: bool = True

    # 数据库配置
    database_url: str = "sqlite:///./data/anyrouter.db"

    # AnyRouter API
    anyrouter_base_url: str = "https://anyrouter.top"
    anyrouter_user_api: str = "/api/user/self"
    anyrouter_sign_api: str = "/api/user/sign_in"
    anyrouter_console_url: str = "/console"

    # 反爬虫配置
    anti_crawler_mask: str = "3000176000856006061501533003690027800375"
    anti_crawler_pos_list: list = [
        15, 35, 29, 24, 33, 16, 1, 38, 10, 9, 19, 31, 40, 27,
        22, 23, 25, 13, 6, 11, 39, 18, 20, 8, 14, 21, 32, 26,
        2, 30, 7, 4, 17, 5, 3, 28, 34, 37, 12, 36
    ]

    # 请求配置
    request_timeout: int = 30
    retry_times: int = 3
    retry_interval: int = 3

    # 配额换算 (1 USD = 500000 quota)
    quota_to_usd_rate: int = 500000

    # JWT 配置
    jwt_secret_key: str = "anyrouter-admin-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # 默认管理员
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"

    class Config:
        env_file = ".env"


settings = Settings()
