"""
new-api 双方案鉴权的离线自检脚本。

用一个假的 new-api 服务替换 HTTP 层，跑通 :func:`execute_with_session_refresh` 的完整链路，
覆盖新旧两套鉴权：

1. 旧方案（``session`` cookie）：请求头 / cookie 必须与改造前一致
2. PAT：只带 ``Authorization``，全程不产生刷新请求
3. refresh 方案：access token 过期 → 自动刷新 → 轮换值落库 → 重试成功
4. refresh 方案：会话被吊销 → 回落账号密码重登
5. 登录方案探测：新版响应写 ``auth_type=new_api_refresh``，旧版仍写 ``session_cookie``
6. 令牌方式无需填 User ID：从校验响应回填
7. API 层：令牌 payload 真正落库，且存的是轮换后的新值
8. 备份往返：令牌凭证不会丢，脱敏导出不含明文

用法::

    cd backend && ./.venv/Scripts/python.exe tools/verify_newapi_auth.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from requests.cookies import cookiejar_from_dict
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import Account, Platform
from app.services import account_session
from app.services.account_session import execute_with_session_refresh, load_auth_data

BASE_URL = "https://fake-newapi.test"
ORIGIN = BASE_URL

_failures: List[str] = []


def check(label: str, actual: Any, expected: Any) -> None:
    ok = actual == expected
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {actual!r}")
    if not ok:
        _failures.append(f"{label}: 期望 {expected!r}，实际 {actual!r}")


def check_true(label: str, value: Any) -> None:
    ok = bool(value)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {value!r}")
    if not ok:
        _failures.append(f"{label}: 期望为真，实际 {value!r}")


# --------------------------------------------------------------------------- 假服务


class FakeNewApi:
    """够用的 new-api 行为替身：JWT 过期、refresh 轮换、重放窗口、会话吊销。"""

    def __init__(self, *, scheme: str = "refresh") -> None:
        self.scheme = scheme
        self.requests: List[Dict[str, Any]] = []
        # sid.vN 形式的 refresh token，每次刷新递增，模拟服务端轮换
        self.refresh_version = 1
        self.valid_refresh = "11111111-1111-4111-8111-111111111111.v1"
        self.issued_jwt: Optional[str] = None
        self.jwt_expires_at = 0
        self.session_revoked = False
        self.valid_pat = "PAT-VALID"
        self.valid_session_cookie = "SESSION-VALID"

    # -- 工具

    def _response(
        self,
        status: int,
        payload: Dict[str, Any],
        cookies: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        response = requests.Response()
        response.status_code = status
        response._content = json.dumps(payload).encode("utf-8")
        response.headers["content-type"] = "application/json"
        response.cookies = cookiejar_from_dict(cookies or {})
        return response

    def _html(self, body: str = "<html>console</html>") -> requests.Response:
        response = requests.Response()
        response.status_code = 200
        response._content = body.encode("utf-8")
        response.headers["content-type"] = "text/html"
        response.cookies = cookiejar_from_dict({})
        return response

    def _issue_jwt(self, ttl: int = 900) -> str:
        self.jwt_expires_at = int(time.time()) + ttl
        self.issued_jwt = f"JWT-v{self.refresh_version}"
        return self.issued_jwt

    def expire_jwt(self) -> None:
        """把已签发的 access token 置为过期，模拟 15 分钟寿命耗尽。"""
        self.jwt_expires_at = int(time.time()) - 10

    # -- 路由

    def handle(self, session: requests.Session, method: str, url: str, **kwargs: Any) -> requests.Response:
        path = urlsplit(url).path
        headers = {k.lower(): v for k, v in (kwargs.get("headers") or {}).items()}
        cookies = dict(kwargs.get("cookies") or {})
        self.requests.append({"method": method, "path": path, "headers": headers, "cookies": cookies})

        if path == "/console":
            return self._html()
        if path == "/api/user/auth/refresh":
            return self._refresh(session, headers)
        if path == "/api/user/login":
            return self._login(session)
        if path == "/api/user/self":
            return self._self(headers, cookies)
        return self._response(404, {"success": False, "message": f"unhandled {path}"})

    def _refresh(self, session: requests.Session, headers: Dict[str, str]) -> requests.Response:
        # SessionCookieOriginGuard
        if headers.get("origin") != ORIGIN and not (headers.get("referer") or "").startswith(ORIGIN):
            return self._response(403, {"success": False, "code": "AUTH_ORIGIN_FORBIDDEN", "message": "bad origin"})
        if self.session_revoked:
            return self._response(401, {"success": False, "code": "AUTH_SESSION_REVOKED", "message": "revoked"})

        cookie_header = headers.get("cookie") or ""
        presented = ""
        for part in cookie_header.split(";"):
            name, _, value = part.strip().partition("=")
            if name == "new_api_refresh":
                presented = value
        if presented != self.valid_refresh:
            return self._response(401, {"success": False, "code": "AUTH_UNAUTHORIZED", "message": "bad refresh"})

        # 轮换：旧值立即失效
        self.refresh_version += 1
        rotated = f"11111111-1111-4111-8111-111111111111.v{self.refresh_version}"
        self.valid_refresh = rotated
        token = self._issue_jwt()
        return self._response(
            200,
            {
                "success": True,
                "message": "",
                "data": {
                    "access_token": token,
                    "token_type": "Bearer",
                    "access_expires_at": self.jwt_expires_at,
                    "session": {"sid": "11111111-1111-4111-8111-111111111111"},
                },
            },
            cookies={"new_api_refresh": rotated},
        )

    def _login(self, session: requests.Session) -> requests.Response:
        self.session_revoked = False
        if self.scheme == "legacy":
            session.cookies.set("session", self.valid_session_cookie)
            return self._response(
                200,
                {"success": True, "message": "", "data": {"id": 858, "username": "tester"}},
                cookies={"session": self.valid_session_cookie},
            )

        self.refresh_version += 1
        rotated = f"11111111-1111-4111-8111-111111111111.v{self.refresh_version}"
        self.valid_refresh = rotated
        session.cookies.set("new_api_refresh", rotated)
        token = self._issue_jwt()
        return self._response(
            200,
            {
                "success": True,
                "message": "",
                "data": {
                    "access_token": token,
                    "token_type": "Bearer",
                    "access_expires_at": self.jwt_expires_at,
                    "session": {"sid": "11111111-1111-4111-8111-111111111111"},
                    "user": {"id": 858, "username": "tester", "quota": 500},
                },
            },
            cookies={"new_api_refresh": rotated},
        )

    def _self(self, headers: Dict[str, str], cookies: Dict[str, str]) -> requests.Response:
        auth = (headers.get("authorization") or "").removeprefix("Bearer ").strip()
        if auth:
            if auth == self.valid_pat:
                return self._ok_user()
            if auth == self.issued_jwt:
                if self.session_revoked:
                    return self._response(
                        401, {"success": False, "code": "AUTH_SESSION_REVOKED", "message": "会话已失效，请重新登录"}
                    )
                if time.time() >= self.jwt_expires_at:
                    return self._response(
                        401, {"success": False, "code": "AUTH_TOKEN_EXPIRED", "message": "登录已过期，请重新登录"}
                    )
                return self._ok_user()
            return self._response(401, {"success": False, "code": "AUTH_UNAUTHORIZED", "message": "无效的访问令牌"})

        if cookies.get("session") == self.valid_session_cookie:
            return self._ok_user()
        return self._response(401, {"success": False, "message": "未登录或登录已过期"})

    def _ok_user(self) -> requests.Response:
        return self._response(
            200,
            {
                "success": True,
                "message": "",
                "data": {
                    "id": 858,
                    "username": "tester",
                    "display_name": "Tester",
                    "quota": 500,
                    "used_quota": 100,
                    "request_count": 7,
                    "group": "default",
                },
            },
        )


def install(server: FakeNewApi) -> Callable[[], None]:
    """把 requests.Session.request 换成假服务；返回还原函数。"""
    original = requests.Session.request

    def fake_request(self, method, url, **kwargs):  # noqa: ANN001
        return server.handle(self, method.upper(), url, **kwargs)

    requests.Session.request = fake_request
    return lambda: setattr(requests.Session, "request", original)


# --------------------------------------------------------------------------- 夹具


def make_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False)()


def make_account(db, **kwargs: Any) -> Account:
    platform = Platform(
        name="Fake New API",
        base_url=BASE_URL,
        adapter_type="new_api",
        sign_mode="api",
    )
    db.add(platform)
    db.commit()
    db.refresh(platform)

    account = Account(anyrouter_user_id=858, platform_id=platform.id, proxy_mode="direct", **kwargs)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def fetch_self(db, account):
    """走真实 funnel 拉一次用户信息。"""
    from app.services.anrouter import anrouter_service

    return execute_with_session_refresh(
        db,
        account,
        lambda credential, user_id, platform: anrouter_service.get_user_info(
            credential,
            user_id,
            platform["base_url"],
            user_api=platform["user_api"],
            console_url=platform["console_url"],
            proxy_mode=account.proxy_mode,
            proxy_url=account.proxy_url,
        ),
    )


# --------------------------------------------------------------------------- 用例


def case_legacy_unchanged() -> None:
    print("\n[1] 旧方案：session cookie + new-api-user，且不带 Authorization")
    server = FakeNewApi(scheme="legacy")
    restore = install(server)
    try:
        db = make_db()
        account = make_account(db, session_cookie=server.valid_session_cookie)
        success, result = fetch_self(db, account)
        check("请求成功", success, True)
        check("拿到 quota", result.get("quota"), 500)

        self_calls = [r for r in server.requests if r["path"] == "/api/user/self"]
        check("self 请求次数", len(self_calls), 1)
        check("携带 session cookie", self_calls[0]["cookies"].get("session"), server.valid_session_cookie)
        check("携带 new-api-user", self_calls[0]["headers"].get("new-api-user"), "858")
        check("不带 Authorization", self_calls[0]["headers"].get("authorization"), None)
        check("未触发刷新", [r for r in server.requests if "refresh" in r["path"]], [])
    finally:
        restore()


def case_pat_no_refresh() -> None:
    print("\n[2] PAT：只带 Authorization，全程零刷新")
    server = FakeNewApi()
    restore = install(server)
    try:
        db = make_db()
        account = make_account(
            db,
            auth_type="bearer",
            auth_data=json.dumps({"token": server.valid_pat}),
        )
        success, result = fetch_self(db, account)
        check("请求成功", success, True)
        check("拿到 quota", result.get("quota"), 500)

        self_calls = [r for r in server.requests if r["path"] == "/api/user/self"]
        check("Authorization 为 PAT", self_calls[0]["headers"].get("authorization"), f"Bearer {server.valid_pat}")
        check("不带 session cookie", self_calls[0]["cookies"].get("session"), None)
        check("未触发刷新", [r for r in server.requests if "refresh" in r["path"]], [])
    finally:
        restore()


def case_refresh_self_heal() -> None:
    print("\n[3] refresh 方案：JWT 过期 → 自动刷新 → 轮换落库 → 重试成功")
    server = FakeNewApi()
    restore = install(server)
    try:
        db = make_db()
        account = make_account(
            db,
            auth_type="new_api_refresh",
            auth_data=json.dumps({"refresh_token": server.valid_refresh}),
        )
        original_refresh = server.valid_refresh

        # 首次请求：没有 access token，惰性刷新拿到一个
        success, result = fetch_self(db, account)
        check("首次请求成功", success, True)
        stored = load_auth_data(account)
        check_true("access_token 已落库", stored.get("access_token"))
        check("refresh_token 已轮换", stored.get("refresh_token") != original_refresh, True)
        check("轮换值与服务端一致", stored.get("refresh_token"), server.valid_refresh)
        refresh_count_1 = len([r for r in server.requests if "refresh" in r["path"]])
        check("刷新次数", refresh_count_1, 1)

        # 第二次请求：缓存内的 JWT 仍有效，不应再刷新
        success, _ = fetch_self(db, account)
        check("第二次请求成功", success, True)
        check(
            "命中缓存未重复刷新",
            len([r for r in server.requests if "refresh" in r["path"]]),
            refresh_count_1,
        )

        # 让服务端认为 JWT 过期：此时缓存里的过期时间仍是未来，会真打出 401
        rotated_before = server.valid_refresh
        server.expire_jwt()
        success, result = fetch_self(db, account)
        check("过期后仍然成功", success, True)
        check("拿到 quota", result.get("quota"), 500)
        check(
            "401 后触发了刷新",
            len([r for r in server.requests if "refresh" in r["path"]]) > refresh_count_1,
            True,
        )
        stored = load_auth_data(account)
        check("再次轮换并落库", stored.get("refresh_token") != rotated_before, True)
        check("与服务端最新值一致", stored.get("refresh_token"), server.valid_refresh)
    finally:
        restore()


def case_refresh_revoked_falls_back_to_login() -> None:
    print("\n[4] refresh 方案：会话被吊销 → 回落账号密码重登")
    server = FakeNewApi()
    restore = install(server)
    try:
        db = make_db()
        account = make_account(
            db,
            auth_type="new_api_refresh",
            auth_data=json.dumps(
                {
                    "refresh_token": server.valid_refresh,
                    "access_token": "JWT-v1",
                    "access_expires_at": int(time.time()) + 900,
                }
            ),
            login_username="tester@example.com",
            login_password="secret",
        )
        server.issued_jwt = "JWT-v1"
        server.jwt_expires_at = int(time.time()) + 900
        server.session_revoked = True

        success, result = fetch_self(db, account)
        check("重登后成功", success, True)
        check("拿到 quota", result.get("quota"), 500)
        check_true("走过登录接口", [r for r in server.requests if r["path"] == "/api/user/login"])
        stored = load_auth_data(account)
        check("登录后 auth_type 仍为 refresh", account.auth_type, "new_api_refresh")
        check("登录后的 refresh_token 与服务端一致", stored.get("refresh_token"), server.valid_refresh)
    finally:
        restore()


def case_login_scheme_detection() -> None:
    print("\n[5] 登录方案探测：新版写 auth_type，旧版写 session_cookie")
    for scheme, expected_type in (("refresh", "new_api_refresh"), ("legacy", None)):
        server = FakeNewApi(scheme=scheme)
        restore = install(server)
        try:
            db = make_db()
            account = make_account(db, login_username="tester@example.com", login_password="secret")
            success, _ = fetch_self(db, account)
            check(f"{scheme} 登录后请求成功", success, True)
            check(f"{scheme} auth_type", account.auth_type, expected_type)
            if expected_type:
                check(f"{scheme} 不留 session_cookie", account.session_cookie, None)
                check_true(f"{scheme} refresh_token 已落库", load_auth_data(account).get("refresh_token"))
            else:
                check(f"{scheme} session_cookie 已落库", account.session_cookie, server.valid_session_cookie)
        finally:
            restore()


def case_user_id_autofill() -> None:
    print("\n[6] 令牌方式无需填 User ID：从校验响应回填")
    from app.api.accounts import prepare_new_api_auth
    from app.services.account_session import build_transient_credential

    for label, auth_type, auth_data in (
        ("PAT", "bearer", {"token": "PAT-VALID"}),
        ("refresh", "new_api_refresh", {"refresh_token": "11111111-1111-4111-8111-111111111111.v1"}),
    ):
        server = FakeNewApi()
        server.valid_refresh = "11111111-1111-4111-8111-111111111111.v1"
        restore = install(server)
        try:
            from app.services.anrouter import anrouter_service

            resolved_type, _, data_dict = prepare_new_api_auth(auth_type, auth_data)
            # 完全不给 user_id，模拟前端只填了令牌
            credential = build_transient_credential(
                BASE_URL, resolved_type, data_dict, "", user_id=None
            )
            success, user_info = anrouter_service.get_user_info(
                credential, "", BASE_URL, user_api="/api/user/self", console_url="/console"
            )
            check(f"{label} 无 user_id 也能校验", success, True)
            check(f"{label} 回填的 User ID", user_info.get("id"), 858)

            self_calls = [r for r in server.requests if r["path"] == "/api/user/self"]
            check(f"{label} 未发送空 new-api-user 头", self_calls[0]["headers"].get("new-api-user"), None)
        finally:
            restore()


def case_api_payload_persists() -> None:
    """覆盖前端只填令牌、不填 User ID / Session Cookie 的提交路径。"""
    print("\n[7] API 层：令牌 payload 必须真正落库")
    from app.api.accounts import _create_account_record
    from app.schemas import AccountCreate

    for label, auth_type, auth_data, expect_key in (
        ("PAT", "bearer", {"token": "PAT-VALID"}, "token"),
        (
            "refresh",
            "new_api_refresh",
            {"refresh_token": "11111111-1111-4111-8111-111111111111.v1"},
            "refresh_token",
        ),
    ):
        server = FakeNewApi()
        server.valid_refresh = "11111111-1111-4111-8111-111111111111.v1"
        restore = install(server)
        try:
            db = make_db()
            platform = Platform(name="Fake", base_url=BASE_URL, adapter_type="new_api", sign_mode="api")
            db.add(platform)
            db.commit()
            db.refresh(platform)

            # 只给令牌：不填 user_id、不填 session_cookie、不填账号密码
            account = _create_account_record(
                db,
                AccountCreate(platform_id=platform.id, auth_type=auth_type, auth_data=auth_data),
            )
            check(f"{label} auth_type 落库", account.auth_type, auth_type)
            stored = load_auth_data(account)
            check_true(f"{label} auth_data.{expect_key} 落库", stored.get(expect_key))
            check(f"{label} User ID 自动回填", account.anyrouter_user_id, 858)
            check(f"{label} 用户名已同步", account.username, "tester")
            if auth_type == "new_api_refresh":
                # 校验时服务端已轮换，落库的必须是新值而不是用户粘贴的旧值
                check(f"{label} 落库的是轮换后的值", stored.get("refresh_token"), server.valid_refresh)
                check(
                    f"{label} 不是用户粘贴的旧值",
                    stored.get("refresh_token") != auth_data["refresh_token"],
                    True,
                )
        finally:
            restore()


def case_backup_roundtrip() -> None:
    """备份导出/恢复必须带上令牌凭证，否则恢复后账号直接掉线。"""
    print("\n[8] 备份往返：令牌凭证不能丢")
    from app.api.backup import VALID_NEW_API_AUTH_TYPES, account_export_data

    for label, auth_type, auth_data in (
        ("PAT", "bearer", {"token": "PAT-VALID"}),
        ("refresh", "new_api_refresh", {"refresh_token": "11111111-1111-4111-8111-111111111111.v9"}),
    ):
        check(f"{label} auth_type 在恢复白名单里", auth_type in VALID_NEW_API_AUTH_TYPES, True)

        db = make_db()
        account = make_account(db, auth_type=auth_type, auth_data=json.dumps(auth_data))
        exported = account_export_data(account, include_credentials=True)
        check(f"{label} 导出带 auth_type", exported.get("auth_type"), auth_type)
        check(f"{label} 导出带 auth_data", exported.get("auth_data"), auth_data)

        # 不带凭证导出时必须脱敏
        redacted = account_export_data(account, include_credentials=False)
        check(f"{label} 脱敏导出不含 auth_data", "auth_data" in redacted, False)


def main() -> int:
    print("=" * 68)
    print("new-api 双方案鉴权自检")
    print("=" * 68)
    case_legacy_unchanged()
    case_pat_no_refresh()
    case_refresh_self_heal()
    case_refresh_revoked_falls_back_to_login()
    case_login_scheme_detection()
    case_user_id_autofill()
    case_api_payload_persists()
    case_backup_roundtrip()

    print("\n" + "=" * 68)
    if _failures:
        print(f"{len(_failures)} 项失败：")
        for item in _failures:
            print(f"  - {item}")
        return 1
    print("全部通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
