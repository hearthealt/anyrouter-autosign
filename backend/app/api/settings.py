"""
系统设置 API
"""
import json
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting, User, AuditAction
from app.schemas import ApiResponse, SettingsResponse, SettingsUpdate
from app.services.scheduler import update_sign_schedule, update_health_check_schedule
from app.services.audit import log_action
from app.api.deps import get_current_user

router = APIRouter(prefix="/settings", tags=["系统设置"])


DEFAULT_SETTINGS = {
    "auto_sign_enabled": False,
    "auto_sign_time": "08:00",
    "health_check_enabled": True,
    "health_check_interval": 6,
    "sign_retry_enabled": True,
    "sign_max_retries": 3,
    "sign_retry_interval": 30,
    "anyrouter_proxy_enabled": False,
    "anyrouter_proxy_url": ""
}


def get_setting(db: Session, key: str, default=None):
    """获取单个设置"""
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        try:
            return json.loads(setting.value)
        except:
            return setting.value
    return default


def set_setting(db: Session, key: str, value):
    """设置单个配置"""
    setting = db.query(Setting).filter(Setting.key == key).first()

    if setting:
        setting.value = json.dumps(value) if not isinstance(value, str) else value
        setting.updated_at = datetime.now()
    else:
        setting = Setting(
            key=key,
            value=json.dumps(value) if not isinstance(value, str) else value
        )
        db.add(setting)


def validate_proxy_url(proxy_url: str):
    """验证代理地址格式，仅支持 HTTP/HTTPS 代理。"""
    parsed = urlsplit(proxy_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="代理地址格式无效，请填写 HTTP/HTTPS 代理地址")


def mask_proxy_url(proxy_url: str) -> str:
    """脱敏代理地址中的认证信息，避免写入审计日志。"""
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
        parsed.fragment
    ))


@router.get("", response_model=ApiResponse)
def get_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    result = {}
    for key, default in DEFAULT_SETTINGS.items():
        result[key] = get_setting(db, key, default)

    return ApiResponse(
        success=True,
        data=SettingsResponse(**result)
    )


@router.put("", response_model=ApiResponse)
def update_settings(
    data: SettingsUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新系统设置"""
    update_data = data.model_dump(exclude_unset=True)
    current_settings = {
        key: get_setting(db, key, default)
        for key, default in DEFAULT_SETTINGS.items()
    }

    if isinstance(update_data.get("anyrouter_proxy_url"), str):
        update_data["anyrouter_proxy_url"] = update_data["anyrouter_proxy_url"].strip()

    merged_settings = {**current_settings, **update_data}
    proxy_enabled = merged_settings.get("anyrouter_proxy_enabled", False)
    proxy_url = merged_settings.get("anyrouter_proxy_url", "")

    if proxy_enabled:
        if not proxy_url:
            raise HTTPException(status_code=400, detail="启用代理时必须填写代理地址")
        validate_proxy_url(proxy_url)

    for key, value in update_data.items():
        if value is not None:
            set_setting(db, key, value)

    db.commit()

    # 更新签到定时任务
    if "auto_sign_enabled" in update_data or "auto_sign_time" in update_data:
        update_sign_schedule()

    # 更新健康检查定时任务
    if "health_check_enabled" in update_data or "health_check_interval" in update_data:
        update_health_check_schedule()

    # 记录审计日志
    audit_detail = update_data.copy()
    if isinstance(audit_detail.get("anyrouter_proxy_url"), str) and audit_detail["anyrouter_proxy_url"]:
        audit_detail["anyrouter_proxy_url"] = mask_proxy_url(audit_detail["anyrouter_proxy_url"])

    log_action(
        db=db,
        action=AuditAction.SETTING_UPDATE,
        user_id=current_user.id,
        username=current_user.username,
        target_type="setting",
        detail=audit_detail,
        request=request
    )

    return ApiResponse(success=True, message="设置保存成功")


@router.get("/scheduler", response_model=ApiResponse)
def get_scheduler_status(db: Session = Depends(get_db)):
    """获取调度器状态"""
    from app.services.scheduler import scheduler

    enabled = get_setting(db, "auto_sign_enabled", False)
    sign_time = get_setting(db, "auto_sign_time", "08:00")

    job = scheduler.get_job("auto_sign")
    next_run = None
    if job and job.next_run_time:
        next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")

    return ApiResponse(success=True, data={
        "enabled": enabled,
        "sign_time": sign_time,
        "next_run": next_run,
        "running": scheduler.running
    })
