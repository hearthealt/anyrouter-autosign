"""数据备份与恢复 API。"""
from __future__ import annotations

import io
import json
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import (
    Account,
    AccountNotify,
    ApiToken,
    AuditAction,
    NotifyChannel,
    Platform,
    Setting,
    SignLog,
    User,
)
from app.schemas import ApiResponse
from app.services.audit import log_action
from app.utils.platform import (
    ADAPTER_TYPE_HTTP,
    DEFAULT_CHECKIN_API,
    DEFAULT_CONSOLE_URL,
    DEFAULT_GROUPS_API,
    DEFAULT_MODELS_API,
    DEFAULT_SIGN_API,
    DEFAULT_STATUS_API,
    DEFAULT_TOKEN_API,
    DEFAULT_USER_API,
    DEFAULT_SIGN_MODE,
    dump_adapter_config,
    normalize_adapter_config,
    normalize_adapter_type,
    normalize_platform_base_url,
    normalize_relative_path,
    validate_public_hostname,
    normalize_sign_mode,
    parse_adapter_config,
)
from app.utils.proxy import normalize_proxy_mode, normalize_proxy_url, validate_proxy_url

router = APIRouter(prefix="/backup", tags=["备份恢复"])

REMOVED_SETTING_KEYS = {
    "anyrouter_proxy_enabled",
    "anyrouter_proxy_url",
    "anrouter_proxy_enabled",
    "anrouter_proxy_url",
}
MAX_BACKUP_BYTES = 10 * 1024 * 1024
MAX_PLATFORMS = 500
MAX_ACCOUNTS = 10_000
MAX_SIGN_LOGS = 100_000
MAX_NOTIFY_CHANNELS = 500
MAX_ACCOUNT_NOTIFIES = 50_000
VALID_AUTH_TYPES = {"none", "custom", "bearer", "cookie", "header", "basic"}



def is_sensitive_setting_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(marker in normalized for marker in (
        "password", "secret", "token", "api_key", "apikey", "webhook", "smtp", "credential"
    ))


def redact_sensitive_config(value: Any, key: str = "") -> Any:
    """移除通用 HTTP 平台配置中可能被硬编码的静态凭证。

    动态模板（例如 ``{{auth.token}}``）不是平台静态凭证，必须保留，
    否则不带凭证的备份导入后会把动态认证模板错误替换成脱敏占位符。
    """
    if isinstance(value, str) and "{{" in value and "}}" in value:
        return value
    normalized_key = key.lower().replace("-", "_")
    if any(marker in normalized_key for marker in (
        "authorization", "cookie", "password", "secret", "token", "api_key", "apikey", "x_api_key"
    )):
        return "__REDACTED__"
    if isinstance(value, dict):
        return {item_key: redact_sensitive_config(item_value, str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [redact_sensitive_config(item) for item in value]
    return value


def contains_redacted_marker(value: Any) -> bool:
    """判断配置中是否包含不带凭证备份产生的脱敏占位符。"""
    if value == "__REDACTED__":
        return True
    if isinstance(value, dict):
        return any(contains_redacted_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_redacted_marker(item) for item in value)
    return False


def backup_includes_credentials(backup_data: dict[str, Any]) -> bool:
    """读取凭证标记，并兼容没有该字段的旧版备份。"""
    marker = backup_data.get("credentials_included")
    if isinstance(marker, bool):
        return marker
    # 旧版备份没有标记，历史行为是导出凭证，因此按包含处理。
    return True


def clean_imported_proxy(proxy_mode: Optional[str], proxy_url: Optional[str]) -> tuple[str, Optional[str]]:
    """清理备份中的账号级代理配置。"""
    mode = "direct" if str(proxy_mode or "").strip().lower() == "global" else normalize_proxy_mode(proxy_mode)
    cleaned_proxy_url = normalize_proxy_url(proxy_url)
    if mode == "custom":
        if not cleaned_proxy_url:
            raise HTTPException(status_code=400, detail="备份中的自定义代理账号缺少代理地址")
        validate_proxy_url(cleaned_proxy_url)
        return mode, cleaned_proxy_url
    return mode, None


def parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"备份中的时间格式无效: {value}") from exc


def parse_auth_data(value: Any) -> Optional[str]:
    if value in (None, "", {}):
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="备份中的 auth_data 不是有效 JSON") from exc
    if not isinstance(value, dict):
        raise HTTPException(status_code=400, detail="备份中的 auth_data 必须是 JSON 对象")
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="备份中的 auth_data 无法序列化") from exc
    if len(encoded.encode("utf-8")) > 64 * 1024:
        raise HTTPException(status_code=400, detail="备份中的 auth_data 不能超过 64KB")
    return encoded


def validate_backup_shape(backup_data: Any) -> dict[str, Any]:
    if not isinstance(backup_data, dict):
        raise HTTPException(status_code=400, detail="备份根节点必须是 JSON 对象")
    if backup_data.get("version") != "1.0":
        raise HTTPException(status_code=400, detail="不支持的备份版本")

    limits = {
        "platforms": MAX_PLATFORMS,
        "accounts": MAX_ACCOUNTS,
        "sign_logs": MAX_SIGN_LOGS,
        "notify_channels": MAX_NOTIFY_CHANNELS,
        "account_notifies": MAX_ACCOUNT_NOTIFIES,
    }
    for key, limit in limits.items():
        value = backup_data.get(key, [])
        if not isinstance(value, list):
            raise HTTPException(status_code=400, detail=f"备份字段 {key} 必须是数组")
        if len(value) > limit:
            raise HTTPException(status_code=400, detail=f"备份字段 {key} 数量不能超过 {limit}")
    return backup_data


def account_export_data(account: Account, include_credentials: bool) -> dict[str, Any]:
    """导出账号。默认不导出任何账号凭证或代理密码。"""
    result = {
        "id": account.id,
        "platform_id": account.platform_id,
        "anyrouter_user_id": account.anyrouter_user_id,
        "anrouter_user_id": account.anyrouter_user_id,
        "external_user_id": account.external_user_id,
        "username": account.username,
        "display_name": account.display_name,
        "note": account.note,
        "proxy_mode": (account.proxy_mode or "direct") if include_credentials else "direct",
        "auth_type": account.auth_type,
        "is_active": account.is_active,
        "health_status": account.health_status,
        "health_message": account.health_message,
        "created_at": account.created_at.isoformat() if account.created_at else None,
    }
    if include_credentials:
        try:
            auth_data = json.loads(account.auth_data) if account.auth_data else None
        except (TypeError, ValueError):
            auth_data = None
        result.update({
            "session_cookie": account.session_cookie,
            "login_username": account.login_username,
            "login_password": account.login_password,
            "auth_type": account.auth_type,
            "auth_data": auth_data,
            "proxy_url": account.proxy_url,
        })
    return result


@router.get("/export", response_class=StreamingResponse)
def export_backup(
    request: Request,
    include_logs: bool = False,
    include_credentials: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导出完整平台配置；凭证只有在显式 include_credentials=true 时才导出。"""
    backup_data: dict[str, Any] = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "credentials_included": include_credentials,
        "platforms": [],
        "accounts": [],
        "settings": [],
        "notify_channels": [],
        "account_notifies": [],
    }

    platforms = db.query(Platform).order_by(Platform.created_at.asc()).all()
    for platform in platforms:
        backup_data["platforms"].append({
            "id": platform.id,
            "name": platform.name,
            "base_url": platform.base_url,
            "adapter_type": platform.adapter_type or "new_api",
            "adapter_config": (
                parse_adapter_config(platform.adapter_config)
                if include_credentials
                else redact_sensitive_config(parse_adapter_config(platform.adapter_config))
            ),
            "sign_mode": platform.sign_mode or DEFAULT_SIGN_MODE,
            "sign_api": platform.sign_api,
            "checkin_api": platform.checkin_api or DEFAULT_CHECKIN_API,
            "user_api": platform.user_api,
            "console_url": platform.console_url,
            "models_api": platform.models_api,
            "groups_api": platform.groups_api,
            "token_api": platform.token_api,
            "status_api": platform.status_api,
            "captcha_api": platform.captcha_api,
            "is_default": bool(platform.is_default),
        })

    for account in db.query(Account).all():
        backup_data["accounts"].append(account_export_data(account, include_credentials))

    for setting in db.query(Setting).all():
        if setting.key in REMOVED_SETTING_KEYS or (not include_credentials and is_sensitive_setting_key(setting.key)):
            continue
        backup_data["settings"].append({"key": setting.key, "value": setting.value})

    for channel in db.query(NotifyChannel).all():
        backup_data["notify_channels"].append({
            "id": channel.id,
            "type": channel.type,
            "name": channel.name,
            "config": channel.config if include_credentials else "{}",
            "is_enabled": channel.is_enabled,
        })

    for relation in db.query(AccountNotify).all():
        backup_data["account_notifies"].append({
            "account_id": relation.account_id,
            "channel_id": relation.channel_id,
            "is_enabled": relation.is_enabled,
            "notify_config": relation.notify_config if include_credentials else "{}",
        })

    if include_logs:
        backup_data["sign_logs"] = []
        logs = db.query(SignLog).order_by(SignLog.sign_time.desc()).limit(1000).all()
        for log in logs:
            backup_data["sign_logs"].append({
                "id": log.id,
                "account_id": log.account_id,
                "sign_time": log.sign_time.isoformat() if log.sign_time else None,
                "success": log.success,
                "message": log.message,
                "reward_quota": log.reward_quota or 0,
                "reward_display": log.reward_display,
                "reward_unit": log.reward_unit,
                "status": log.status,
                "retry_count": log.retry_count or 0,
            })

    log_action(
        db=db,
        action=AuditAction.BACKUP_EXPORT,
        user_id=current_user.id,
        username=current_user.username,
        target_type="backup",
        detail={
            "include_logs": include_logs,
            "include_credentials": include_credentials,
            "platforms": len(backup_data["platforms"]),
            "accounts": len(backup_data["accounts"]),
        },
        request=request,
    )

    content = json.dumps(backup_data, ensure_ascii=False, indent=2).encode("utf-8")
    buffer = io.BytesIO(content)
    filename = f"anyrouter_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import", response_model=ApiResponse)
async def import_backup(
    request: Request,
    file: UploadFile = File(...),
    overwrite: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """导入备份，兼容旧版 AnyRouter 备份和新版 HTTP 平台备份。"""
    content = await file.read(MAX_BACKUP_BYTES + 1)
    if len(content) > MAX_BACKUP_BYTES:
        raise HTTPException(status_code=413, detail=f"备份文件不能超过 {MAX_BACKUP_BYTES // (1024 * 1024)}MB")
    try:
        backup_data = validate_backup_shape(json.loads(content.decode("utf-8")))
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="备份文件必须使用 UTF-8 编码") from exc
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail=f"无效的备份文件格式：第 {exc.lineno} 行") from exc

    imported_counts = {
        "platforms": 0,
        "accounts": 0,
        "settings": 0,
        "notify_channels": 0,
        "account_notifies": 0,
        "sign_logs": 0,
    }
    credentials_included = backup_includes_credentials(backup_data)
    import_warnings: list[str] = []

    try:
        platform_id_map: dict[Any, int] = {}
        for item in backup_data.get("platforms", []):
            old_id = item.get("id")
            if old_id is None:
                raise HTTPException(status_code=400, detail="备份中的平台缺少 id")
            try:
                adapter_type = normalize_adapter_type(item.get("adapter_type", "new_api"))
                adapter_config = normalize_adapter_config(adapter_type, item.get("adapter_config") or {})
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"平台配置无效: {exc}") from exc

            name = str(item.get("name") or "").strip()
            base_url = str(item.get("base_url") or "").strip()
            if not name or not base_url:
                raise HTTPException(status_code=400, detail="备份中的平台缺少名称或 Base URL")
            existing = db.query(Platform).filter(Platform.name == name).first()
            redacted_adapter_config = contains_redacted_marker(adapter_config)
            try:
                base_url = normalize_platform_base_url(base_url)
                validate_public_hostname(base_url, allow_private=settings.allow_private_platform_urls)
                values = {
                    "base_url": base_url,
                    "adapter_type": adapter_type,
                    "adapter_config": dump_adapter_config(adapter_config),
                    "sign_mode": normalize_sign_mode(item.get("sign_mode", DEFAULT_SIGN_MODE)),
                    "sign_api": normalize_relative_path(item.get("sign_api"), DEFAULT_SIGN_API),
                    "checkin_api": normalize_relative_path(item.get("checkin_api"), DEFAULT_CHECKIN_API),
                    "user_api": normalize_relative_path(item.get("user_api"), DEFAULT_USER_API),
                    "console_url": normalize_relative_path(item.get("console_url"), DEFAULT_CONSOLE_URL),
                    "models_api": normalize_relative_path(item.get("models_api"), DEFAULT_MODELS_API),
                    "groups_api": normalize_relative_path(item.get("groups_api"), DEFAULT_GROUPS_API),
                    "token_api": normalize_relative_path(item.get("token_api"), DEFAULT_TOKEN_API),
                    "status_api": normalize_relative_path(item.get("status_api"), DEFAULT_STATUS_API),
                    "captcha_api": normalize_relative_path(item.get("captcha_api"), "", optional=True),
                    "is_default": bool(item.get("is_default", False)),
                }
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=f"平台 {name} 配置无效: {exc}") from exc
            if existing:
                platform_id_map[old_id] = existing.id
                if overwrite:
                    for key, value in values.items():
                        # 不带凭证的备份不能用脱敏占位符覆盖本机已有静态凭证。
                        if key == "adapter_config" and not credentials_included and redacted_adapter_config:
                            if normalize_adapter_type(existing.adapter_type) == adapter_type:
                                continue
                            import_warnings.append(f"平台 {name} 的适配器类型发生变化，但静态凭证未随备份导出")
                        setattr(existing, key, value)
                    imported_counts["platforms"] += 1
            else:
                new_platform = Platform(name=name, **values)
                db.add(new_platform)
                db.flush()
                platform_id_map[old_id] = new_platform.id
                imported_counts["platforms"] += 1
                if not credentials_included and redacted_adapter_config:
                    import_warnings.append(f"平台 {name} 含有脱敏静态凭证，新平台导入后需要重新填写")

        if backup_data.get("platforms") and overwrite and any(item.get("is_default") for item in backup_data["platforms"]):
            default_id = next((platform_id_map[item.get("id")] for item in backup_data["platforms"] if item.get("is_default") and item.get("id") in platform_id_map), None)
            if default_id:
                db.query(Platform).filter(Platform.id != default_id).update({"is_default": False})

        for item in backup_data.get("settings", []):
            key = str(item.get("key") or "")
            if not key or key in REMOVED_SETTING_KEYS:
                continue
            existing = db.query(Setting).filter(Setting.key == key).first()
            if existing:
                if overwrite:
                    existing.value = item.get("value")
                    imported_counts["settings"] += 1
            else:
                db.add(Setting(key=key, value=item.get("value")))
                imported_counts["settings"] += 1

        channel_id_map: dict[Any, int] = {}
        for item in backup_data.get("notify_channels", []):
            old_id = item.get("id")
            name = str(item.get("name") or "").strip()
            if old_id is None or not name:
                raise HTTPException(status_code=400, detail="备份中的推送渠道缺少 id 或名称")
            existing = db.query(NotifyChannel).filter(NotifyChannel.name == name).first()
            incoming_config = item.get("config")
            if existing:
                channel_id_map[old_id] = existing.id
                if overwrite:
                    existing.type = item.get("type") or existing.type
                    if credentials_included:
                        existing.config = incoming_config or "{}"
                    # 默认备份中的 {} 只表示“未导出凭证”，不能覆盖已有渠道配置。
                    existing.is_enabled = bool(item.get("is_enabled", True))
                    imported_counts["notify_channels"] += 1
            else:
                channel = NotifyChannel(
                    type=item.get("type") or "custom",
                    name=name,
                    config=(incoming_config or "{}") if credentials_included else "{}",
                    is_enabled=bool(item.get("is_enabled", True)) if credentials_included else False,
                )
                db.add(channel)
                db.flush()
                channel_id_map[old_id] = channel.id
                imported_counts["notify_channels"] += 1

        account_id_map: dict[Any, int] = {}
        for item in backup_data.get("accounts", []):
            old_id = item.get("id")
            imported_platform_id = item.get("platform_id")
            mapped_platform_id = platform_id_map.get(imported_platform_id)
            if old_id is None or mapped_platform_id is None:
                raise HTTPException(status_code=400, detail="备份中的账号缺少有效的平台信息")
            platform = db.query(Platform).filter(Platform.id == mapped_platform_id).first()
            if not platform:
                raise HTTPException(status_code=400, detail="备份中的账号平台不存在")
            adapter_type = normalize_adapter_type(platform.adapter_type)
            proxy_mode, proxy_url = clean_imported_proxy(item.get("proxy_mode"), item.get("proxy_url"))

            imported_user_id: Optional[int] = None
            imported_external_id = str(item.get("external_user_id") or "").strip() or None
            if adapter_type != ADAPTER_TYPE_HTTP:
                raw_user_id = item.get("anyrouter_user_id", item.get("anrouter_user_id", item.get("user_id")))
                if raw_user_id not in (None, ""):
                    try:
                        imported_user_id = int(raw_user_id)
                    except (TypeError, ValueError) as exc:
                        raise HTTPException(status_code=400, detail=f"账号 {old_id} 的 User ID 无效") from exc
                if imported_external_id is None and imported_user_id is not None:
                    imported_external_id = str(imported_user_id)
                existing_query = db.query(Account).filter(Account.platform_id == mapped_platform_id)
                if imported_user_id is not None:
                    existing = existing_query.filter(Account.anyrouter_user_id == imported_user_id).first()
                elif imported_external_id:
                    existing = existing_query.filter(Account.external_user_id == imported_external_id).first()
                else:
                    existing = None
                auth_type = None
                auth_data = None
            else:
                existing_query = db.query(Account).filter(Account.platform_id == mapped_platform_id)
                existing = existing_query.filter(Account.external_user_id == imported_external_id).first() if imported_external_id else None
                auth_type = str(item.get("auth_type") or "none").strip().lower()
                if auth_type not in VALID_AUTH_TYPES:
                    raise HTTPException(status_code=400, detail=f"账号 {old_id} 的认证方式无效")
                auth_data = parse_auth_data(item.get("auth_data")) if credentials_included else None
                if not credentials_included and existing:
                    auth_type = existing.auth_type or auth_type
                    auth_data = existing.auth_data

            if not credentials_included and existing:
                proxy_mode = existing.proxy_mode or "direct"
                proxy_url = existing.proxy_url
            supplied_session_cookie = credentials_included and "session_cookie" in item
            supplied_login = credentials_included and ("login_username" in item or "login_password" in item)
            has_new_api_credentials = bool(item.get("session_cookie")) or bool(item.get("login_username") and item.get("login_password"))
            has_http_credentials = auth_type == "none" or bool(auth_data)
            requested_active = bool(item.get("is_active", True))
            credentials_available = has_http_credentials if adapter_type == ADAPTER_TYPE_HTTP else has_new_api_credentials
            account_values = {
                "platform_id": mapped_platform_id,
                "username": str(item.get("username") or imported_external_id or f"{platform.name} 账号"),
                "display_name": item.get("display_name"),
                "note": item.get("note"),
                "proxy_mode": proxy_mode,
                "proxy_url": proxy_url,
                "is_active": requested_active and credentials_available,
                "health_status": item.get("health_status") or "unknown",
                "health_message": item.get("health_message"),
            }
            if not credentials_included and existing:
                account_values["is_active"] = existing.is_active
            if adapter_type == ADAPTER_TYPE_HTTP:
                account_values.update({
                    "external_user_id": imported_external_id,
                    "auth_type": auth_type,
                    "auth_data": auth_data,
                    "anyrouter_user_id": None,
                })
            else:
                account_values.update({
                    "anyrouter_user_id": imported_user_id,
                    "external_user_id": imported_external_id,
                    "auth_type": None,
                    "auth_data": None,
                })

            if existing:
                account_id_map[old_id] = existing.id
                if overwrite:
                    for key, value in account_values.items():
                        setattr(existing, key, value)
                    if supplied_session_cookie:
                        existing.session_cookie = item.get("session_cookie") or ""
                    if supplied_login:
                        existing.login_username = item.get("login_username")
                        existing.login_password = item.get("login_password")
                    imported_counts["accounts"] += 1
            else:
                new_account = Account(
                    session_cookie=item.get("session_cookie") or "",
                    login_username=item.get("login_username"),
                    login_password=item.get("login_password"),
                    **account_values,
                )
                db.add(new_account)
                db.flush()
                account_id_map[old_id] = new_account.id
                imported_counts["accounts"] += 1

        for item in backup_data.get("account_notifies", []):
            account_id = account_id_map.get(item.get("account_id"))
            channel_id = channel_id_map.get(item.get("channel_id"))
            if not account_id or not channel_id:
                continue
            relation = db.query(AccountNotify).filter(
                AccountNotify.account_id == account_id,
                AccountNotify.channel_id == channel_id,
            ).first()
            if relation:
                if overwrite:
                    relation.is_enabled = bool(item.get("is_enabled", True))
                    if credentials_included:
                        relation.notify_config = item.get("notify_config") or relation.notify_config
                    imported_counts["account_notifies"] += 1
            else:
                db.add(AccountNotify(
                    account_id=account_id,
                    channel_id=channel_id,
                    is_enabled=bool(item.get("is_enabled", True)),
                    notify_config=(item.get("notify_config") or "{}") if credentials_included else "{}",
                ))
                imported_counts["account_notifies"] += 1

        for item in backup_data.get("sign_logs", []):
            account_id = account_id_map.get(item.get("account_id"))
            if not account_id:
                continue
            sign_time = parse_datetime(item.get("sign_time")) or datetime.now()
            existing = db.query(SignLog).filter(
                SignLog.account_id == account_id,
                SignLog.sign_time == sign_time,
                SignLog.message == item.get("message"),
            ).first()
            values = {
                "account_id": account_id,
                "sign_time": sign_time,
                "success": bool(item.get("success", False)),
                "message": item.get("message"),
                "reward_quota": int(item.get("reward_quota") or 0),
                "reward_display": item.get("reward_display"),
                "reward_unit": item.get("reward_unit") or "quota",
                "status": item.get("status") or ("success" if item.get("success") else "failed"),
                "retry_count": int(item.get("retry_count") or 0),
            }
            if existing:
                if overwrite:
                    for key, value in values.items():
                        setattr(existing, key, value)
                    imported_counts["sign_logs"] += 1
            else:
                db.add(SignLog(**values))
                imported_counts["sign_logs"] += 1

        db.commit()
        log_action(
            db=db,
            action=AuditAction.BACKUP_IMPORT,
            user_id=current_user.id,
            username=current_user.username,
            target_type="backup",
            detail={"overwrite": overwrite, "imported": imported_counts},
            request=request,
        )
        result_data = {**imported_counts, "credentials_included": credentials_included}
        if import_warnings:
            result_data["warnings"] = import_warnings
        return ApiResponse(success=True, message="数据导入成功", data=result_data)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"导入失败: {exc}") from exc


@router.get("/info", response_model=ApiResponse)
def get_backup_info(db: Session = Depends(get_db)):
    """获取当前数据统计信息。"""
    return ApiResponse(
        success=True,
        data={
            "platform_count": db.query(Platform).count(),
            "account_count": db.query(Account).count(),
            "sign_log_count": db.query(SignLog).count(),
            "notify_channel_count": db.query(NotifyChannel).count(),
            "setting_count": db.query(Setting).count(),
        },
    )
