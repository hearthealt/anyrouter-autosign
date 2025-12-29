"""
系统设置 API
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Setting
from app.schemas import ApiResponse, SettingsResponse, SettingsUpdate
from app.services.scheduler import update_sign_schedule, update_health_check_schedule

router = APIRouter(prefix="/settings", tags=["系统设置"])


DEFAULT_SETTINGS = {
    "auto_sign_enabled": False,
    "auto_sign_time": "08:00",
    "health_check_enabled": True,
    "health_check_interval": 6,
    "sign_retry_enabled": True,
    "sign_max_retries": 3,
    "sign_retry_interval": 30
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
def update_settings(data: SettingsUpdate, db: Session = Depends(get_db)):
    """更新系统设置"""
    update_data = data.model_dump(exclude_unset=True)

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
