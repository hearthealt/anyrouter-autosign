"""可配置 HTTP 签到适配器。

该适配器只支持数据映射、占位符替换和有限响应规则，不执行 Jinja/Python
表达式，避免平台配置演变成远程代码执行入口。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
from urllib.parse import urljoin, urlsplit

import requests
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Account
from app.services.adapters.base import AdapterCapabilities
from app.utils.platform import ADAPTER_TYPE_HTTP, validate_public_hostname

_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
_MISSING = object()
_REDIRECT_CODES = {301, 302, 303, 307, 308}


def parse_json_object(value: Any, field_name: str = "JSON") -> Dict[str, Any]:
    if value is None or value == "":
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{field_name} 不是有效 JSON: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"{field_name} 必须是 JSON 对象")
        return parsed
    raise ValueError(f"{field_name} 必须是 JSON 对象")


def get_path(data: Any, path: Optional[str], default: Any = None) -> Any:
    """读取简单 dotted path，支持列表下标，不支持表达式。"""
    if path is None or path == "" or path == "$":
        return data

    normalized = str(path).strip()
    if normalized.startswith("$."):
        normalized = normalized[2:]

    current = data
    for part in normalized.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                return default
            current = current[part]
            continue
        if isinstance(current, (list, tuple)):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return default
            continue
        return default
    return current


def _resolve_context(context: Mapping[str, Any], path: str) -> Any:
    value = get_path(context, path, _MISSING)
    if value is _MISSING:
        raise ValueError(f"模板变量不存在: {path}")
    return value


def render_template(value: Any, context: Mapping[str, Any]) -> Any:
    """递归渲染 JSON 数据中的 {{auth.token}} 变量。"""
    if isinstance(value, dict):
        return {str(key): render_template(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render_template(item, context) for item in value]
    if not isinstance(value, str):
        return value

    full_match = _PLACEHOLDER.fullmatch(value)
    if full_match:
        return _resolve_context(context, full_match.group(1))

    def replace(match: re.Match[str]) -> str:
        resolved = _resolve_context(context, match.group(1))
        if resolved is None:
            return ""
        if isinstance(resolved, (dict, list)):
            return json.dumps(resolved, ensure_ascii=False, separators=(",", ":"))
        return str(resolved)

    return _PLACEHOLDER.sub(replace, value)


def evaluate_rule(payload: Any, rule: Any) -> bool:
    """执行受限响应判断规则。列表规则按任意一个匹配处理。"""
    if isinstance(rule, list):
        return any(evaluate_rule(payload, item) for item in rule)
    if not isinstance(rule, Mapping):
        return bool(rule)

    value = get_path(payload, rule.get("path"), _MISSING)
    if "exists" in rule:
        return (value is not _MISSING) is bool(rule["exists"])
    if value is _MISSING:
        return False
    if "equals" in rule:
        return value == rule["equals"]
    if "not_equals" in rule:
        return value != rule["not_equals"]
    if "truthy" in rule:
        return bool(value) is bool(rule["truthy"])
    if "falsy" in rule:
        return (not bool(value)) is bool(rule["falsy"])
    if "contains" in rule:
        return str(rule["contains"]) in str(value)
    if "not_contains" in rule:
        return str(rule["not_contains"]) not in str(value)
    if "regex" in rule:
        return re.search(str(rule["regex"]), str(value)) is not None
    if "in" in rule and isinstance(rule["in"], Iterable) and not isinstance(rule["in"], (str, bytes)):
        return value in rule["in"]
    return bool(value)


def _safe_number(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_reward(raw_value: float, unit: str) -> str:
    number = int(raw_value) if raw_value.is_integer() else round(raw_value, 4)
    if not unit:
        return str(number)
    if unit in {"$", "¥", "￥"}:
        return f"{unit}{number}"
    return f"{number} {unit}"


class ConfigurableHttpAdapter:
    adapter_type = ADAPTER_TYPE_HTTP
    capabilities = AdapterCapabilities(supports_health_check=False)

    def _build_context(self, account: Account) -> Dict[str, Any]:
        auth_data = parse_json_object(account.auth_data, "账号 auth_data")
        return {
            "auth": auth_data,
            "account": {
                "id": account.id,
                "external_user_id": account.external_user_id or "",
                "username": account.username or "",
                "display_name": account.display_name or "",
                "session_cookie": account.session_cookie or "",
                "login_username": account.login_username or "",
                "login_password": account.login_password or "",
            },
        }

    @staticmethod
    def _apply_common_auth(
        account: Account,
        auth_data: Dict[str, Any],
        headers: Dict[str, Any],
        cookies: Dict[str, Any],
        request_kwargs: Dict[str, Any],
    ) -> None:
        auth_type = (account.auth_type or "custom").strip().lower()
        if auth_type == "bearer":
            token = auth_data.get("token")
            if token and "Authorization" not in headers:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "cookie":
            if isinstance(auth_data.get("cookies"), Mapping):
                cookies.update(auth_data["cookies"])
            elif auth_data.get("cookie") and "Cookie" not in headers:
                headers["Cookie"] = str(auth_data["cookie"])
        elif auth_type == "header":
            if isinstance(auth_data.get("headers"), Mapping):
                headers.update(auth_data["headers"])
            elif auth_data.get("name"):
                headers[str(auth_data["name"])] = str(auth_data.get("value", ""))
        elif auth_type == "basic":
            username = auth_data.get("username")
            password = auth_data.get("password")
            if username is not None and password is not None:
                request_kwargs["auth"] = (str(username), str(password))

    @staticmethod
    def _request_with_redirect_validation(
        session: requests.Session,
        method: str,
        url: str,
        follow_redirects: bool,
        max_redirects: int,
        request_kwargs: Dict[str, Any],
    ) -> requests.Response:
        current_url = url
        current_method = method
        for redirect_index in range(max_redirects + 1):
            validate_public_hostname(
                current_url,
                allow_private=settings.allow_private_platform_urls,
                resolve_dns=True,
            )
            response = session.request(
                current_method,
                current_url,
                allow_redirects=False,
                **request_kwargs,
            )
            if response.status_code not in _REDIRECT_CODES or not response.headers.get("Location"):
                return response
            if not follow_redirects:
                return response
            if redirect_index >= max_redirects:
                raise requests.TooManyRedirects("重定向次数超过平台配置上限")

            next_url = urljoin(current_url, response.headers["Location"])
            current_origin = urlsplit(current_url)
            next_origin = urlsplit(next_url)
            if (
                current_origin.scheme.lower(),
                current_origin.hostname,
                current_origin.port,
            ) != (
                next_origin.scheme.lower(),
                next_origin.hostname,
                next_origin.port,
            ):
                raise requests.RequestException("拒绝携带账号凭证跳转到其他站点")
            current_url = next_url
            if response.status_code == 303:
                current_method = "GET"
                request_kwargs.pop("json", None)
                request_kwargs.pop("data", None)

        raise requests.TooManyRedirects("重定向次数超过平台配置上限")

    def sign(
        self,
        db: Session,
        account: Account,
        platform_config: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        del db  # 当前通用适配器不修改数据库会话
        config = platform_config.get("adapter_config") or {}
        request_config = config.get("request") or {}
        response_config = config.get("response") or {}

        try:
            context = self._build_context(account)
            context["platform"] = {"base_url": platform_config["base_url"]}

            method = str(request_config.get("method") or "POST").upper()
            path = str(render_template(request_config.get("path") or "", context))
            url = f"{platform_config['base_url'].rstrip('/')}/{path.lstrip('/')}"

            headers = render_template(request_config.get("headers") or {}, context)
            query = render_template(request_config.get("query") or {}, context)
            body = render_template(request_config.get("body"), context)
            if not isinstance(headers, dict) or not isinstance(query, dict):
                raise ValueError("headers/query 渲染结果必须是 JSON 对象")

            headers.setdefault("Accept", "application/json, text/plain, */*")
            headers.setdefault("User-Agent", "Universal-Checkin/1.0")
            cookies: Dict[str, Any] = {}
            request_kwargs: Dict[str, Any] = {
                "headers": headers,
                "params": query,
                "cookies": cookies,
                "timeout": min(max(int(request_config.get("timeout") or settings.request_timeout), 1), 120),
            }
            self._apply_common_auth(account, context["auth"], headers, cookies, request_kwargs)

            body_type = str(request_config.get("body_type") or "json").lower()
            if method not in {"GET", "DELETE"} and body_type != "none" and body is not None:
                if body_type == "json":
                    request_kwargs["json"] = body
                elif body_type == "form":
                    request_kwargs["data"] = body
                elif body_type == "raw":
                    request_kwargs["data"] = body if isinstance(body, (str, bytes)) else json.dumps(body, ensure_ascii=False)

            session = requests.Session()
            if (account.proxy_mode or "direct") == "custom" and account.proxy_url:
                session.proxies.update({"http": account.proxy_url, "https": account.proxy_url})

            response = self._request_with_redirect_validation(
                session,
                method,
                url,
                bool(request_config.get("follow_redirects", False)),
                min(max(int(request_config.get("max_redirects") or 3), 0), 5),
                request_kwargs,
            )

            try:
                payload: Any = response.json()
            except ValueError:
                payload = {"text": response.text, "status_code": response.status_code}
            if isinstance(payload, dict):
                payload.setdefault("_http_status", response.status_code)

            success_rule = response_config.get("success") or response_config.get("success_rule")
            already_rule = response_config.get("already_signed") or response_config.get("already_signed_rule")
            success = evaluate_rule(payload, success_rule) if success_rule is not None else response.ok
            already_signed = evaluate_rule(payload, already_rule) if already_rule is not None else False

            message_path = response_config.get("message_path")
            message_value = get_path(payload, message_path, "") if message_path else ""
            if not message_value and isinstance(payload, Mapping):
                message_value = payload.get("message") or payload.get("msg") or payload.get("text") or ""
            message = str(message_value or "").strip()

            reward_raw = get_path(payload, response_config.get("reward_path"), 0)
            reward_number = _safe_number(reward_raw)
            multiplier = _safe_number(response_config.get("reward_multiplier", 1)) or 1.0
            normalized_reward = reward_number * multiplier
            reward_quota = int(round(normalized_reward))
            reward_unit = str(response_config.get("reward_unit") or "count").strip() or "count"
            reward_display_path = response_config.get("reward_display_path")
            reward_display = (
                str(get_path(payload, reward_display_path, "") or "").strip()
                if reward_display_path
                else _format_reward(normalized_reward, reward_unit)
            )

            if already_signed:
                success = True
                message = message or "今日已签到"
            elif success:
                message = message or "签到成功"
            else:
                message = message or f"签到失败（HTTP {response.status_code}）"

            return True, {
                "success": bool(success),
                "message": message,
                "reward_quota": reward_quota,
                "reward_display": reward_display,
                "reward_unit": reward_unit,
                "already_signed": bool(already_signed),
                "raw": payload,
                "http_status": response.status_code,
            }
        except (ValueError, TypeError) as exc:
            return False, {
                "success": False,
                "message": f"HTTP 适配器配置错误: {exc}",
                "reward_quota": 0,
                "reward_unit": "count",
                "already_signed": False,
            }
        except requests.RequestException as exc:
            return False, {
                "success": False,
                "message": f"网络请求失败: {exc}",
                "reward_quota": 0,
                "reward_unit": "count",
                "already_signed": False,
            }
