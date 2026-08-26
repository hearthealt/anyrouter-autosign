"""
New API 面板凭证抽象。

新版 new-api 把面板鉴权从「``session`` cookie + ``new-api-user`` 头」换成了：

- **access token**：HS256 JWT，走 ``Authorization: Bearer``，寿命 15 分钟
- **refresh token**：HttpOnly cookie ``new_api_refresh``（``<sid>.<secret>``），寿命 30 天，
  但每次刷新都会轮换，旧值只有 30 秒重放窗口，超窗后复用会导致整个登录会话被吊销
- **PAT（系统访问令牌）**：账号级随机串，永不过期，同样走 ``Authorization``

本模块把「凭证」抽象成对象，让 :mod:`app.services.anrouter` 里所有对外方法
不用感知具体方案。旧方案由 :class:`LegacySessionCredential` 承载，行为与改造前完全一致。

刷新动作通过构造时注入的 ``refresher`` 回调完成，避免与 ``anrouter`` 形成循环导入。
"""
from __future__ import annotations

import base64
import binascii
import json
import logging
import time
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

SCHEME_LEGACY_COOKIE = "cookie"
SCHEME_PAT = "bearer"
SCHEME_REFRESH = "new_api_refresh"

# 服务端 service.AccessTokenTTL = 15min；提前续期，避免边界上打到 401
ACCESS_TOKEN_SKEW_SECONDS = 60

# 服务端 writeDashboardAuthError / authSessionErrorCode 会返回这些码
AUTH_CODE_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
AUTH_CODE_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
AUTH_CODE_SESSION_REVOKED = "AUTH_SESSION_REVOKED"
AUTH_CODE_SESSION_MISMATCH = "AUTH_SESSION_MISMATCH"
AUTH_CODE_REFRESH_RACE = "AUTH_REFRESH_RACE"
AUTH_CODE_ORIGIN_FORBIDDEN = "AUTH_ORIGIN_FORBIDDEN"

# 这些错误说明会话已经不可恢复，只能回落到账号密码重新登录
UNRECOVERABLE_AUTH_CODES = frozenset(
    {AUTH_CODE_UNAUTHORIZED, AUTH_CODE_SESSION_REVOKED, AUTH_CODE_SESSION_MISMATCH}
)

# 刷新成功后回调的载荷键
ROTATE_KEY_REFRESH_TOKEN = "refresh_token"
ROTATE_KEY_ACCESS_TOKEN = "access_token"
ROTATE_KEY_ACCESS_EXPIRES_AT = "access_expires_at"


class NewApiAuthError(RuntimeError):
    """面板鉴权失败。``code`` 是 new-api 返回的错误码，便于上层区分处理。"""

    def __init__(self, message: str, code: str = "", status: int = 0) -> None:
        super().__init__(message)
        self.code = (code or "").strip()
        self.status = status

    @property
    def needs_relogin(self) -> bool:
        return self.code in UNRECOVERABLE_AUTH_CODES


# refresher(refresh_token) -> {"access_token", "access_expires_at", "refresh_token"}
Refresher = Callable[[str], Dict[str, Any]]
# on_rotate(payload) -> None，用于把轮换后的令牌落盘
RotateCallback = Callable[[Dict[str, Any]], None]


def decode_access_token_expiry(access_token: str) -> int:
    """从 JWT 的 ``exp`` claim 取过期时间；解析不出来返回 0。

    用户可能直接粘贴一个 access_token，这样也能算出剩余寿命，不必当成永久有效。
    """
    token = (access_token or "").strip()
    if not token:
        return 0
    parts = token.split(".")
    if len(parts) != 3:
        return 0
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        claims = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, ValueError):
        return 0
    expires_at = claims.get("exp") if isinstance(claims, dict) else None
    try:
        return int(expires_at or 0)
    except (TypeError, ValueError):
        return 0


@runtime_checkable
class DashboardCredential(Protocol):
    """`anrouter` 里所有对外方法共用的凭证协议。"""

    scheme: str

    def auth_headers(self) -> Dict[str, str]:
        """需要附加到请求头上的鉴权字段。"""
        ...

    def seed_cookies(self) -> Dict[str, str]:
        """请求的初始 cookie（旧方案是 ``session``，新方案为空）。"""
        ...

    def handle_unauthorized(self, code: str = "") -> bool:
        """收到鉴权失败后尝试自愈；返回 True 表示可以原样重试一次。"""
        ...

    @property
    def is_usable(self) -> bool:
        """是否携带了可用于发请求的凭证内容。"""
        ...

    @property
    def needs_relogin(self) -> bool:
        """凭证已经彻底失效，必须用账号密码重新登录。"""
        ...


class _BaseCredential:
    """共享 ``new-api-user`` 头与不可恢复标记。"""

    scheme = ""

    def __init__(self, user_id: Optional[str] = None) -> None:
        self.user_id = str(user_id) if user_id not in (None, "") else ""
        self._needs_relogin = False

    def _user_headers(self) -> Dict[str, str]:
        # 新方案的服务端从令牌里取身份，不读这个头；保留是为了兼容旧站点
        return {"new-api-user": self.user_id} if self.user_id else {}

    def seed_cookies(self) -> Dict[str, str]:
        return {}

    def handle_unauthorized(self, code: str = "") -> bool:
        return False

    def mark_needs_relogin(self) -> None:
        self._needs_relogin = True

    @property
    def is_usable(self) -> bool:
        return False

    @property
    def needs_relogin(self) -> bool:
        return self._needs_relogin


class LegacySessionCredential(_BaseCredential):
    """旧版 new-api：``session`` cookie + ``new-api-user`` 头。

    请求头与 cookie 必须与改造前逐字节一致，否则老站点会回归。
    """

    scheme = SCHEME_LEGACY_COOKIE

    def __init__(self, session_cookie: str, user_id: Optional[str] = None) -> None:
        super().__init__(user_id)
        self.session_cookie = session_cookie or ""

    def auth_headers(self) -> Dict[str, str]:
        return self._user_headers()

    def seed_cookies(self) -> Dict[str, str]:
        return {"session": self.session_cookie}

    @property
    def is_usable(self) -> bool:
        return bool(self.session_cookie.strip())

    def handle_unauthorized(self, code: str = "") -> bool:
        # 旧方案没有刷新通道，只能交给上层的账号密码重登
        self.mark_needs_relogin()
        return False


class PatCredential(_BaseCredential):
    """系统访问令牌（PAT）：永不过期，无状态，不需要刷新。"""

    scheme = SCHEME_PAT

    def __init__(self, pat: str, user_id: Optional[str] = None) -> None:
        super().__init__(user_id)
        self.pat = (pat or "").strip()

    def auth_headers(self) -> Dict[str, str]:
        headers = self._user_headers()
        if self.pat:
            headers["authorization"] = f"Bearer {self.pat}"
        return headers

    @property
    def is_usable(self) -> bool:
        return bool(self.pat)

    def handle_unauthorized(self, code: str = "") -> bool:
        # PAT 只会因为被重新签发或账号被禁而失效，重试没有意义
        self.mark_needs_relogin()
        return False


class RefreshCredential(_BaseCredential):
    """refresh cookie 换 15 分钟 JWT，并把轮换后的新 refresh token 落盘。

    :param refresher: ``(refresh_token) -> {"access_token", "access_expires_at", "refresh_token"}``
        由调用方注入（通常是 ``anrouter_service.refresh_dashboard_token``），避免循环导入
    :param on_rotate: 刷新成功后的落盘回调。**必须实现**，否则轮换后的令牌一丢，账号就掉线
    """

    scheme = SCHEME_REFRESH

    def __init__(
        self,
        refresh_token: str,
        refresher: Refresher,
        *,
        access_token: str = "",
        access_expires_at: int = 0,
        user_id: Optional[str] = None,
        on_rotate: Optional[RotateCallback] = None,
    ) -> None:
        super().__init__(user_id)
        self.refresh_token = (refresh_token or "").strip()
        self._refresher = refresher
        self._on_rotate = on_rotate
        self._access_token = (access_token or "").strip()
        self._access_expires_at = int(access_expires_at or 0)
        if self._access_token and self._access_expires_at <= 0:
            # 只给了 access_token 没给过期时间时，从 JWT 自己的 exp 里补
            self._access_expires_at = decode_access_token_expiry(self._access_token)
        self.last_error: Optional[NewApiAuthError] = None

    # ------------------------------------------------------------------ 令牌状态

    @property
    def access_token(self) -> str:
        return self._access_token

    @property
    def access_expires_at(self) -> int:
        return self._access_expires_at

    @property
    def is_usable(self) -> bool:
        return bool(self.refresh_token or self._access_token)

    def _access_token_usable(self) -> bool:
        if not self._access_token:
            return False
        if self._access_expires_at <= 0:
            # 过期时间未知时当作可用，让服务端来判定
            return True
        return time.time() < self._access_expires_at - ACCESS_TOKEN_SKEW_SECONDS

    # -------------------------------------------------------------------- 刷新

    def ensure_fresh(self) -> bool:
        """需要时刷新 access token。返回 False 表示当前拿不到可用令牌。"""
        if self._access_token_usable():
            return True
        return self._refresh()

    def _refresh(self) -> bool:
        if not self.refresh_token:
            self.last_error = NewApiAuthError("缺少 refresh token", code=AUTH_CODE_UNAUTHORIZED)
            self.mark_needs_relogin()
            return False

        try:
            result = self._refresher(self.refresh_token)
        except NewApiAuthError as exc:
            self.last_error = exc
            if exc.needs_relogin:
                self.mark_needs_relogin()
            logger.warning("刷新面板 access token 失败: code=%s, %s", exc.code or "N/A", exc)
            return False

        access_token = str(result.get(ROTATE_KEY_ACCESS_TOKEN) or "").strip()
        if not access_token:
            self.last_error = NewApiAuthError("刷新成功但响应里没有 access_token")
            return False

        self._access_token = access_token
        expires_at = int(result.get(ROTATE_KEY_ACCESS_EXPIRES_AT) or 0)
        self._access_expires_at = expires_at or decode_access_token_expiry(access_token)

        # 关键：服务端在响应里 Set-Cookie 了一个新的 new_api_refresh，旧值即将失效
        rotated = str(result.get(ROTATE_KEY_REFRESH_TOKEN) or "").strip()
        if rotated:
            self.refresh_token = rotated

        self.last_error = None
        self._persist()
        return True

    def _persist(self) -> None:
        if self._on_rotate is None:
            logger.warning("RefreshCredential 未配置 on_rotate，轮换后的 refresh token 不会被保存")
            return
        try:
            self._on_rotate(
                {
                    ROTATE_KEY_REFRESH_TOKEN: self.refresh_token,
                    ROTATE_KEY_ACCESS_TOKEN: self._access_token,
                    ROTATE_KEY_ACCESS_EXPIRES_AT: self._access_expires_at,
                }
            )
        except Exception:
            # 落盘失败不能吃掉本次请求，但必须留痕：下次刷新会因旧值失效而掉线
            logger.exception("保存轮换后的 refresh token 失败，账号可能在下次刷新时掉线")

    # -------------------------------------------------------------- 凭证协议实现

    def auth_headers(self) -> Dict[str, str]:
        # 尽力刷新；拿不到令牌也照常发请求，让服务端返回标准 401，
        # 交由既有的错误处理链路生成用户可读的消息
        self.ensure_fresh()
        headers = self._user_headers()
        if self._access_token:
            headers["authorization"] = f"Bearer {self._access_token}"
        return headers

    def handle_unauthorized(self, code: str = "") -> bool:
        normalized = (code or "").strip()
        if normalized in UNRECOVERABLE_AUTH_CODES and normalized != AUTH_CODE_UNAUTHORIZED:
            # 会话被吊销/不匹配，刷新也救不回来
            self.mark_needs_relogin()
            return False
        # access token 过期是常态；AUTH_UNAUTHORIZED 也可能只是 JWT 已失效，值得试一次
        self._access_token = ""
        self._access_expires_at = 0
        return self._refresh()


def build_credential(
    auth_type: Optional[str],
    auth_data: Optional[Dict[str, Any]],
    session_cookie: Optional[str],
    user_id: Optional[str] = None,
    *,
    refresher: Optional[Refresher] = None,
    on_rotate: Optional[RotateCallback] = None,
) -> DashboardCredential:
    """按账号上存的认证方式构造凭证。

    未识别的 ``auth_type`` 一律回落到旧方案，保证老账号行为不变。
    """
    scheme = (auth_type or "").strip().lower()
    data = auth_data or {}

    if scheme == SCHEME_REFRESH:
        if refresher is None:
            raise ValueError("refresh 方案必须注入 refresher")
        return RefreshCredential(
            str(data.get(ROTATE_KEY_REFRESH_TOKEN) or ""),
            refresher,
            access_token=str(data.get(ROTATE_KEY_ACCESS_TOKEN) or ""),
            access_expires_at=int(data.get(ROTATE_KEY_ACCESS_EXPIRES_AT) or 0),
            user_id=user_id,
            on_rotate=on_rotate,
        )

    if scheme == SCHEME_PAT:
        return PatCredential(str(data.get("token") or ""), user_id=user_id)

    return LegacySessionCredential(session_cookie or "", user_id=user_id)
