"""
new-api 新版鉴权辅助工具（JWT access token + 轮换式 refresh cookie）。

新版 new-api 已经不再用 `session` cookie + `new-api-user` 头，改成了：

- access token：HS256 JWT，放 `Authorization: Bearer <jwt>`，**寿命只有 15 分钟**
- refresh token：HttpOnly cookie `new_api_refresh`，格式 `<sid>.<secret>`，寿命 30 天，
  但**每次刷新都会轮换**，旧值只有 30 秒重放窗口，超时后再用旧值会被判定为令牌重用，
  整个登录会话直接吊销（浏览器也会被登出）
- PAT（系统访问令牌）：账号级的随机字符串，存在 `users.access_token`，**永不过期**，
  同样放 `Authorization` 头即可，是自动化脚本最省事的方案

因此本模块提供两条路：

1. `NewApiClient(base_url, pat=...)`         —— 推荐，无状态，不用管过期
2. `NewApiClient(base_url, refresh_token=..., state_path=...)`
                                             —— 用 refresh cookie 自动换 JWT，
                                                轮换后的新值会落盘，必须持久化

命令行用法::

    # 用账号密码登录，签发一个永不过期的 PAT（只需要做一次）
    python newapi_auth.py pat --base-url https://api.example.com -u USER -p PASS

    # 用 PAT 拉取用量数据
    python newapi_auth.py data --base-url https://api.example.com --pat XXXX

    # 用 refresh cookie 拉取用量数据（会把轮换后的新 cookie 写回 state 文件）
    python newapi_auth.py data --base-url https://api.example.com \
        --refresh-token "9f3963e9-....dd69df9b..." --state .newapi_state.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlsplit

import requests

REFRESH_COOKIE_NAME = "new_api_refresh"
REFRESH_PATH = "/api/user/auth/refresh"
PAT_PATH = "/api/user/token"
LOGIN_PATH = "/api/user/login"

# 服务端 service.AccessTokenTTL = 15min；提前 60s 续期，避免边界上打到 401
ACCESS_TOKEN_SKEW_SECONDS = 60
# 服务端 service.RefreshReplayWindow = 30s，窗口内用同一个旧 token 重试是幂等的
REFRESH_RACE_RETRY_SECONDS = 2

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0"
)


class NewApiAuthError(RuntimeError):
    """鉴权失败。`code` 是 new-api 返回的错误码，便于上层区分处理。"""

    def __init__(self, message: str, code: str = "", status: int = 0) -> None:
        super().__init__(message)
        self.code = code
        self.status = status

    @property
    def needs_relogin(self) -> bool:
        """会话已经不可恢复，只能重新用账号密码登录。"""
        return self.code in {"AUTH_SESSION_REVOKED", "AUTH_UNAUTHORIZED", "AUTH_SESSION_MISMATCH"}


def _origin_of(base_url: str) -> str:
    parts = urlsplit(base_url)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"base_url 需要是完整地址，收到: {base_url!r}")
    return f"{parts.scheme}://{parts.netloc}"


def _error_from_response(response: requests.Response) -> NewApiAuthError:
    code = ""
    message = ""
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    if isinstance(payload, dict):
        code = str(payload.get("code") or "")
        message = str(payload.get("message") or "")
    return NewApiAuthError(
        message or f"HTTP {response.status_code}",
        code=code,
        status=response.status_code,
    )


class NewApiClient:
    """封装 new-api 新版鉴权的 HTTP 客户端。

    :param base_url: 站点根地址，例如 ``https://api.example.com``
    :param pat: 系统访问令牌（永不过期）。给了它就不会走 refresh 流程
    :param refresh_token: ``new_api_refresh`` cookie 的值，格式 ``<sid>.<secret>``
    :param state_path: 轮换后的 refresh token 落盘位置。走 refresh 流程时**强烈建议**传
    """

    def __init__(
        self,
        base_url: str,
        *,
        pat: Optional[str] = None,
        refresh_token: Optional[str] = None,
        state_path: Optional[str | os.PathLike[str]] = None,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: float = 20.0,
        proxies: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.origin = _origin_of(self.base_url)
        self.timeout = timeout
        self.pat = (pat or "").strip() or None
        self.state_path = Path(state_path) if state_path else None

        self._refresh_token = (refresh_token or "").strip() or None
        self._access_token: Optional[str] = None
        self._access_expires_at: int = 0

        self._session = requests.Session()
        # cookie 的 Path 是 /api/user/auth，交给 cookiejar 容易踩路径匹配的坑，
        # 这里统一手工拼 Cookie 头
        self._session.headers.update(
            {
                "accept": "application/json, text/plain, */*",
                "user-agent": user_agent,
                "cache-control": "no-store",
            }
        )
        if proxies:
            self._session.proxies.update(proxies)

        self._load_state()
        if not self.pat and not self._refresh_token:
            raise ValueError("至少要提供 pat 或 refresh_token 之一")

    # ------------------------------------------------------------------ 状态持久化

    def _load_state(self) -> None:
        """从 state 文件恢复 refresh token。文件里的值优先于构造参数。"""
        if not self.state_path or not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(state, dict):
            return
        stored = str(state.get("refresh_token") or "").strip()
        if stored:
            self._refresh_token = stored
        stored_access = str(state.get("access_token") or "").strip()
        expires_at = state.get("access_expires_at")
        if stored_access and isinstance(expires_at, int):
            self._access_token = stored_access
            self._access_expires_at = expires_at

    def _save_state(self) -> None:
        if not self.state_path:
            return
        payload = {
            "refresh_token": self._refresh_token,
            "access_token": self._access_token,
            "access_expires_at": self._access_expires_at,
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.state_path)
        try:
            os.chmod(self.state_path, 0o600)
        except OSError:
            # Windows 上 chmod 语义有限，失败不影响功能
            pass

    # ---------------------------------------------------------------------- 令牌

    @property
    def refresh_token(self) -> Optional[str]:
        """当前有效的 refresh token（可能已被轮换过）。"""
        return self._refresh_token

    def _access_token_valid(self) -> bool:
        return bool(self._access_token) and time.time() < self._access_expires_at - ACCESS_TOKEN_SKEW_SECONDS

    def _bearer(self) -> str:
        if self.pat:
            return self.pat
        if not self._access_token_valid():
            self.refresh_access_token()
        return self._access_token or ""

    def refresh_access_token(self) -> str:
        """用 refresh cookie 换一个新的 access token，并保存轮换后的 refresh token。"""
        if not self._refresh_token:
            raise NewApiAuthError("没有可用的 refresh token，请重新登录", code="AUTH_UNAUTHORIZED")

        response = self._post_refresh()
        if response.status_code == 409 and _error_code(response) == "AUTH_REFRESH_RACE":
            # 30s 重放窗口内用同一个旧 token 重试，服务端会返回同一份轮换结果
            time.sleep(REFRESH_RACE_RETRY_SECONDS)
            response = self._post_refresh()

        if response.status_code != 200:
            error = _error_from_response(response)
            if error.needs_relogin:
                self._refresh_token = None
                self._save_state()
            raise error

        payload = response.json()
        data = payload.get("data") or {}
        access_token = str(data.get("access_token") or "")
        if not access_token:
            raise NewApiAuthError("刷新成功但响应里没有 access_token")

        self._access_token = access_token
        self._access_expires_at = int(data.get("access_expires_at") or 0)

        # 关键：服务端在响应里 Set-Cookie 了一个**新的** new_api_refresh，旧值即将失效
        rotated = response.cookies.get(REFRESH_COOKIE_NAME)
        if rotated:
            self._refresh_token = rotated
        self._save_state()
        return access_token

    def _post_refresh(self) -> requests.Response:
        return self._session.post(
            f"{self.base_url}{REFRESH_PATH}",
            headers={
                # SessionCookieOriginGuard 要求 Origin 或 Referer 等于站点自身 origin，
                # 少了这个头会直接 403 AUTH_ORIGIN_FORBIDDEN
                "origin": self.origin,
                "referer": f"{self.origin}/",
                "cookie": f"{REFRESH_COOKIE_NAME}={self._refresh_token}",
            },
            timeout=self.timeout,
        )

    # ---------------------------------------------------------------------- 请求

    def request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """发起已鉴权的请求；access token 过期时自动刷新并重试一次。"""
        url = path if path.startswith("http") else f"{self.base_url}{path}"
        headers = dict(kwargs.pop("headers", None) or {})
        headers["authorization"] = f"Bearer {self._bearer()}"
        headers.setdefault("referer", f"{self.origin}/")

        response = self._session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
        if response.status_code != 401 or self.pat:
            return response

        if _error_code(response) not in {"AUTH_TOKEN_EXPIRED", "AUTH_UNAUTHORIZED"}:
            return response

        self.refresh_access_token()
        headers["authorization"] = f"Bearer {self._bearer()}"
        return self._session.request(method, url, headers=headers, timeout=self.timeout, **kwargs)

    def get_json(self, path: str, **kwargs: Any) -> Any:
        response = self.request("GET", path, **kwargs)
        if response.status_code != 200:
            raise _error_from_response(response)
        return response.json()

    # -------------------------------------------------------------- 常用业务接口

    def self_info(self) -> Dict[str, Any]:
        return self.get_json("/api/user/self")["data"]

    def usage(self, start_timestamp: int, end_timestamp: int, default_time: str = "hour") -> Any:
        """对应你原来那个 /api/data/self 请求。"""
        return self.get_json(
            "/api/data/self",
            params={
                "start_timestamp": str(start_timestamp),
                "end_timestamp": str(end_timestamp),
                "default_time": default_time,
            },
        )["data"]

    def issue_pat(self) -> str:
        """签发一个新的系统访问令牌（永不过期）。会让该账号旧的 PAT 立即失效。"""
        return str(self.get_json(PAT_PATH)["data"])


def _is_json(response: requests.Response) -> bool:
    return "application/json" in (response.headers.get("content-type") or "")


def _error_code(response: requests.Response) -> str:
    """安全地取出 new-api 的错误码，非 JSON 响应返回空串。"""
    if not _is_json(response):
        return ""
    try:
        payload = response.json()
    except ValueError:
        return ""
    return str(payload.get("code") or "") if isinstance(payload, dict) else ""


def login(
    base_url: str,
    username: str,
    password: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: float = 20.0,
) -> Dict[str, Any]:
    """账号密码登录，返回 ``{access_token, refresh_token, access_expires_at, sid, user}``。

    注意：登录会新建一个登录会话，服务端对活跃会话数和签发频率都有上限
    （``AUTH_SESSION_LIMIT`` / ``AUTH_SESSION_ISSUANCE_LIMIT``），别拿它当轮询手段。
    """
    origin = _origin_of(base_url)
    response = requests.post(
        f"{base_url.rstrip('/')}{LOGIN_PATH}",
        json={"username": username, "password": password},
        headers={
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "user-agent": user_agent,
            "origin": origin,
            "referer": f"{origin}/login",
        },
        timeout=timeout,
    )
    if response.status_code != 200:
        raise _error_from_response(response)
    payload = response.json()
    if not payload.get("success"):
        raise NewApiAuthError(str(payload.get("message") or "登录失败"), code=str(payload.get("code") or ""))

    data = payload.get("data") or {}
    return {
        "access_token": data.get("access_token"),
        "access_expires_at": data.get("access_expires_at"),
        "refresh_token": response.cookies.get(REFRESH_COOKIE_NAME),
        "sid": (data.get("session") or {}).get("sid"),
        "user": data.get("user"),
    }


# --------------------------------------------------------------------------- CLI


def _build_client(args: argparse.Namespace) -> NewApiClient:
    return NewApiClient(
        args.base_url,
        pat=args.pat,
        refresh_token=args.refresh_token,
        state_path=args.state,
    )


def _cmd_pat(args: argparse.Namespace) -> int:
    bundle = login(args.base_url, args.username, args.password)
    client = NewApiClient(args.base_url, refresh_token=bundle["refresh_token"], state_path=args.state)
    client._access_token = bundle["access_token"]
    client._access_expires_at = int(bundle["access_expires_at"] or 0)
    pat = client.issue_pat()
    print("系统访问令牌（永不过期，请妥善保存；重新签发会让这个失效）:")
    print(pat)
    return 0


def _cmd_data(args: argparse.Namespace) -> int:
    client = _build_client(args)
    end = args.end or int(time.time())
    start = args.start or end - 86400
    print(json.dumps(client.usage(start, end, args.default_time), ensure_ascii=False, indent=2))
    return 0


def _cmd_self(args: argparse.Namespace) -> int:
    client = _build_client(args)
    print(json.dumps(client.self_info(), ensure_ascii=False, indent=2))
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="new-api 新版鉴权辅助工具")
    parser.add_argument("--base-url", required=True, help="站点根地址，如 https://api.example.com")
    parser.add_argument("--pat", default=None, help="系统访问令牌")
    parser.add_argument("--refresh-token", default=None, help="new_api_refresh cookie 的值")
    parser.add_argument("--state", default=None, help="refresh token 轮换后的落盘路径")

    sub = parser.add_subparsers(dest="command", required=True)

    pat_parser = sub.add_parser("pat", help="用账号密码登录并签发系统访问令牌")
    pat_parser.add_argument("-u", "--username", required=True)
    pat_parser.add_argument("-p", "--password", required=True)
    pat_parser.set_defaults(func=_cmd_pat)

    data_parser = sub.add_parser("data", help="拉取 /api/data/self 用量数据")
    data_parser.add_argument("--start", type=int, default=None, help="起始时间戳，默认 24h 前")
    data_parser.add_argument("--end", type=int, default=None, help="结束时间戳，默认现在")
    data_parser.add_argument("--default-time", default="hour", choices=["hour", "day"])
    data_parser.set_defaults(func=_cmd_data)

    self_parser = sub.add_parser("self", help="拉取 /api/user/self 账号信息")
    self_parser.set_defaults(func=_cmd_self)

    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except NewApiAuthError as exc:
        hint = "，需要重新用账号密码登录" if exc.needs_relogin else ""
        print(f"鉴权失败: {exc} (code={exc.code or 'N/A'}, status={exc.status}){hint}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
