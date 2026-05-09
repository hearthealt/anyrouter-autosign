"""
平台配置工具
"""
from typing import Any, Dict

DEFAULT_BASE_URL = "https://anyrouter.top"
DEFAULT_SIGN_API = "/api/user/sign_in"
DEFAULT_CHECKIN_API = "/api/user/checkin"
DEFAULT_USER_API = "/api/user/self"
DEFAULT_CONSOLE_URL = "/console"
DEFAULT_MODELS_API = "/api/user/models"
DEFAULT_GROUPS_API = "/api/user/self/groups"
DEFAULT_TOKEN_API = "/api/token/"
DEFAULT_STATUS_API = "/api/status"
DEFAULT_SIGN_MODE = "api"
SIGN_MODE_API = "api"
SIGN_MODE_LOGIN = "login"
VALID_SIGN_MODES = {SIGN_MODE_API, SIGN_MODE_LOGIN}


def _normalize_base_url(value: str) -> str:
    base_url = (value or DEFAULT_BASE_URL).strip()
    return base_url.rstrip("/")


def _normalize_path(value: str, default: str) -> str:
    path = (value or default).strip()
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/":
        path = path.rstrip("/")
    return path


def normalize_sign_mode(value: str) -> str:
    """标准化平台签到模式。"""
    mode = (value or DEFAULT_SIGN_MODE).strip().lower()
    return mode if mode in VALID_SIGN_MODES else DEFAULT_SIGN_MODE


def get_platform_config(platform: Any) -> Dict[str, str]:
    """获取平台请求配置。"""
    if platform is None:
        raise ValueError("平台不存在")
    return {
        "base_url": _normalize_base_url(getattr(platform, "base_url", DEFAULT_BASE_URL)),
        "sign_mode": normalize_sign_mode(getattr(platform, "sign_mode", DEFAULT_SIGN_MODE)),
        "sign_api": _normalize_path(getattr(platform, "sign_api", DEFAULT_SIGN_API), DEFAULT_SIGN_API),
        "checkin_api": _normalize_path(getattr(platform, "checkin_api", DEFAULT_CHECKIN_API), DEFAULT_CHECKIN_API),
        "user_api": _normalize_path(getattr(platform, "user_api", DEFAULT_USER_API), DEFAULT_USER_API),
        "console_url": _normalize_path(getattr(platform, "console_url", DEFAULT_CONSOLE_URL), DEFAULT_CONSOLE_URL),
        "models_api": _normalize_path(getattr(platform, "models_api", DEFAULT_MODELS_API), DEFAULT_MODELS_API),
        "groups_api": _normalize_path(getattr(platform, "groups_api", DEFAULT_GROUPS_API), DEFAULT_GROUPS_API),
        "token_api": _normalize_path(getattr(platform, "token_api", DEFAULT_TOKEN_API), DEFAULT_TOKEN_API),
        "status_api": _normalize_path(getattr(platform, "status_api", DEFAULT_STATUS_API), DEFAULT_STATUS_API),
    }


def get_account_platform_config(account: Any) -> Dict[str, str]:
    """获取账号所属平台的请求配置，不再兼容无平台账号。"""
    if not getattr(account, "platform_id", None) or not getattr(account, "platform", None):
        raise ValueError("账号未配置平台")
    return get_platform_config(account.platform)
