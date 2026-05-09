"""
代理配置工具
"""
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

from fastapi import HTTPException

ACCOUNT_PROXY_MODES = {"global", "direct", "custom"}
DEFAULT_ACCOUNT_PROXY_MODE = "global"


def normalize_proxy_mode(value: Optional[str]) -> str:
    """规范化账号代理模式。"""
    mode = (value or DEFAULT_ACCOUNT_PROXY_MODE).strip().lower()
    if mode not in ACCOUNT_PROXY_MODES:
        raise HTTPException(status_code=400, detail="代理模式无效")
    return mode


def normalize_proxy_url(value: Optional[str]) -> Optional[str]:
    """清理代理地址。"""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def validate_proxy_url(proxy_url: str) -> None:
    """验证代理地址格式，仅支持 HTTP/HTTPS 代理。"""
    parsed = urlsplit(proxy_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="代理地址格式无效，请填写 HTTP/HTTPS 代理地址")


def mask_proxy_url(proxy_url: str) -> str:
    """脱敏代理地址中的认证信息，避免写入日志或接口响应。"""
    parsed = urlsplit(proxy_url)
    if not parsed.username or parsed.password is None:
        return proxy_url

    host = parsed.hostname or ""
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port:
        host = f"{host}:{parsed.port}"

    return urlunsplit((
        parsed.scheme,
        f"{parsed.username}:***@{host}",
        parsed.path,
        parsed.query,
        parsed.fragment,
    ))
