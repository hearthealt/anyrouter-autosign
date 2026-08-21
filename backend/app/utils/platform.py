"""
平台配置工具。

平台分为两类适配器：
- new_api: 兼容现有 AnyRouter/New API 协议；
- http: 通过受限 JSON 配置描述请求和响应规则。
"""
from __future__ import annotations

import ipaddress
import json
import socket
from typing import Any, Dict, Mapping
from urllib.parse import urlsplit, urlunsplit

DEFAULT_BASE_URL = "https://anyrouter.top"
DEFAULT_SIGN_API = "/api/user/sign_in"
DEFAULT_CHECKIN_API = "/api/user/checkin"
DEFAULT_USER_API = "/api/user/self"
DEFAULT_CONSOLE_URL = "/console"
DEFAULT_MODELS_API = "/api/user/models"
DEFAULT_GROUPS_API = "/api/user/self/groups"
DEFAULT_TOKEN_API = "/api/token/"
DEFAULT_STATUS_API = "/api/status"
DEFAULT_CAPTCHA_API = ""
DEFAULT_SIGN_MODE = "api"
SIGN_MODE_API = "api"
SIGN_MODE_LOGIN = "login"
VALID_SIGN_MODES = {SIGN_MODE_API, SIGN_MODE_LOGIN}

ADAPTER_TYPE_NEW_API = "new_api"
ADAPTER_TYPE_HTTP = "http"
DEFAULT_ADAPTER_TYPE = ADAPTER_TYPE_NEW_API
VALID_ADAPTER_TYPES = {ADAPTER_TYPE_NEW_API, ADAPTER_TYPE_HTTP}

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


def normalize_adapter_type(value: str | None) -> str:
    """标准化平台适配器类型。"""
    adapter_type = (value or DEFAULT_ADAPTER_TYPE).strip().lower()
    if adapter_type not in VALID_ADAPTER_TYPES:
        raise ValueError(f"不支持的适配器类型: {adapter_type}")
    return adapter_type


def normalize_platform_base_url(value: str | None) -> str:
    """校验并标准化平台 Base URL。"""
    base_url = (value or "").strip()
    if not base_url:
        raise ValueError("Base URL 不能为空")

    parsed = urlsplit(base_url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Base URL 仅支持有效的 HTTP/HTTPS 地址")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Base URL 不允许包含用户名或密码")
    if parsed.query or parsed.fragment:
        raise ValueError("Base URL 不允许包含 query 或 fragment")

    normalized_path = parsed.path.rstrip("/")
    netloc = parsed.netloc.lower()
    return urlunsplit((parsed.scheme.lower(), netloc, normalized_path, "", ""))


def validate_public_hostname(
    base_url: str,
    allow_private: bool = False,
    *,
    resolve_dns: bool = False,
) -> None:
    """拒绝本机、链路本地、私网和保留地址。

    配置保存阶段只检查显式 IP；真正发请求前启用 resolve_dns，避免域名解析
    到内网地址后绕过检查。
    """
    if allow_private:
        return

    hostname = urlsplit(base_url).hostname
    if not hostname:
        raise ValueError("Base URL 缺少主机名")
    if hostname.lower() == "localhost":
        raise ValueError("默认不允许访问 localhost")

    def ensure_public(address_value: str) -> None:
        address = ipaddress.ip_address(address_value)
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            raise ValueError("默认不允许访问本机、私网或保留地址")

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        if not resolve_dns:
            return
        try:
            addresses = {item[4][0] for item in socket.getaddrinfo(hostname, None)}
        except socket.gaierror as exc:
            raise ValueError(f"无法解析平台域名: {hostname}") from exc
        for address in addresses:
            ensure_public(address)
    else:
        ensure_public(hostname)


def _normalize_base_url(value: str) -> str:
    return normalize_platform_base_url(value or DEFAULT_BASE_URL)


def normalize_relative_path(value: str | None, default: str = "", *, optional: bool = False) -> str:
    """标准化平台接口路径，并禁止使用绝对 URL 绕过 Base URL。"""
    raw_value = value if value is not None else default
    path = str(raw_value or "").strip()
    if not path and optional:
        return ""
    if not path:
        path = default
    if not path:
        raise ValueError("接口路径不能为空")

    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc or path.startswith("//"):
        raise ValueError("接口配置必须是相对路径，不能填写完整 URL")
    if parsed.fragment:
        raise ValueError("接口路径不允许包含 fragment")
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/":
        path = path.rstrip("/")
    return path


def _normalize_path(value: str, default: str) -> str:
    return normalize_relative_path(value, default)


def _normalize_optional_str(value: str, default: str = "") -> str:
    return (value or default).strip()


def normalize_sign_mode(value: str) -> str:
    """标准化平台签到模式。"""
    mode = (value or DEFAULT_SIGN_MODE).strip().lower()
    return mode if mode in VALID_SIGN_MODES else DEFAULT_SIGN_MODE


def parse_adapter_config(value: Any) -> Dict[str, Any]:
    """把数据库 JSON 文本或 API 字典转换为普通字典。"""
    if value is None or value == "":
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"适配器配置不是有效 JSON: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError("适配器配置必须是 JSON 对象")
        return parsed
    raise ValueError("适配器配置必须是 JSON 对象")


def dump_adapter_config(value: Any) -> str:
    """序列化适配器配置，保持数据库字段稳定。"""
    return json.dumps(parse_adapter_config(value), ensure_ascii=False, separators=(",", ":"))


def validate_http_adapter_config(value: Any) -> Dict[str, Any]:
    """校验通用 HTTP 适配器的安全、最小配置。"""
    config = parse_adapter_config(value)
    request_config = config.get("request")
    if not isinstance(request_config, dict):
        raise ValueError("HTTP 适配器必须配置 request 对象")

    method = str(request_config.get("method") or "POST").upper()
    if method not in HTTP_METHODS:
        raise ValueError(f"不支持的请求方法: {method}")
    request_config["method"] = method
    request_config["path"] = normalize_relative_path(request_config.get("path"), "")

    body_type = str(request_config.get("body_type") or "json").lower()
    if body_type not in {"json", "form", "raw", "none"}:
        raise ValueError("body_type 仅支持 json/form/raw/none")
    request_config["body_type"] = body_type

    for key in ("headers", "query"):
        if key in request_config and not isinstance(request_config[key], dict):
            raise ValueError(f"request.{key} 必须是 JSON 对象")

    response_config = config.get("response", {})
    if not isinstance(response_config, dict):
        raise ValueError("response 必须是 JSON 对象")

    config["request"] = request_config
    config["response"] = response_config
    return config


def normalize_adapter_config(adapter_type: str, value: Any) -> Dict[str, Any]:
    """按适配器类型校验配置。"""
    normalized_type = normalize_adapter_type(adapter_type)
    if normalized_type == ADAPTER_TYPE_HTTP:
        return validate_http_adapter_config(value)
    return parse_adapter_config(value)


def get_platform_config(platform: Any) -> Dict[str, Any]:
    """获取平台请求配置。"""
    if platform is None:
        raise ValueError("平台不存在")

    adapter_type = normalize_adapter_type(getattr(platform, "adapter_type", DEFAULT_ADAPTER_TYPE))
    return {
        "base_url": _normalize_base_url(getattr(platform, "base_url", DEFAULT_BASE_URL)),
        "adapter_type": adapter_type,
        "adapter_config": normalize_adapter_config(adapter_type, getattr(platform, "adapter_config", {})),
        "sign_mode": normalize_sign_mode(getattr(platform, "sign_mode", DEFAULT_SIGN_MODE)),
        "sign_api": _normalize_path(getattr(platform, "sign_api", DEFAULT_SIGN_API), DEFAULT_SIGN_API),
        "checkin_api": _normalize_path(getattr(platform, "checkin_api", DEFAULT_CHECKIN_API), DEFAULT_CHECKIN_API),
        "user_api": _normalize_path(getattr(platform, "user_api", DEFAULT_USER_API), DEFAULT_USER_API),
        "console_url": _normalize_path(getattr(platform, "console_url", DEFAULT_CONSOLE_URL), DEFAULT_CONSOLE_URL),
        "models_api": _normalize_path(getattr(platform, "models_api", DEFAULT_MODELS_API), DEFAULT_MODELS_API),
        "groups_api": _normalize_path(getattr(platform, "groups_api", DEFAULT_GROUPS_API), DEFAULT_GROUPS_API),
        "token_api": _normalize_path(getattr(platform, "token_api", DEFAULT_TOKEN_API), DEFAULT_TOKEN_API),
        "status_api": _normalize_path(getattr(platform, "status_api", DEFAULT_STATUS_API), DEFAULT_STATUS_API),
        "captcha_api": normalize_relative_path(
            getattr(platform, "captcha_api", DEFAULT_CAPTCHA_API),
            DEFAULT_CAPTCHA_API,
            optional=True,
        ),
    }


def get_account_platform_config(account: Any) -> Dict[str, Any]:
    """获取账号所属平台的请求配置，不再兼容无平台账号。"""
    if not getattr(account, "platform_id", None) or not getattr(account, "platform", None):
        raise ValueError("账号未配置平台")
    return get_platform_config(account.platform)
