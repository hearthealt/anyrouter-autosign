"""跨平台签到奖励聚合工具。"""
from __future__ import annotations

from typing import Any, MutableMapping

from app.config import settings

QUOTA_REWARD_UNIT = "quota"
DEFAULT_REWARD_UNIT = "count"


def normalize_reward_unit(unit: Any, *, adapter_type: str | None = None) -> str:
    value = str(unit or "").strip()
    if value:
        return value
    return QUOTA_REWARD_UNIT if adapter_type in (None, "new_api") else DEFAULT_REWARD_UNIT


def add_reward_total(
    totals: MutableMapping[str, float],
    reward_quota: int | float,
    reward_unit: str | None,
    *,
    adapter_type: str | None = None,
) -> None:
    """按单位累加奖励；New API quota 会转换成美元数值。"""
    try:
        amount = float(reward_quota or 0)
    except (TypeError, ValueError):
        return
    if amount == 0:
        return
    unit = normalize_reward_unit(reward_unit, adapter_type=adapter_type)
    if unit == QUOTA_REWARD_UNIT:
        key = "$"
        amount /= settings.quota_to_usd_rate
    else:
        key = unit
    totals[key] = totals.get(key, 0.0) + amount


def serialize_reward_totals(totals: MutableMapping[str, float]) -> dict[str, int | float]:
    result: dict[str, int | float] = {}
    for unit, raw_value in totals.items():
        value = round(float(raw_value), 4)
        result[unit] = int(value) if value.is_integer() else value
    return result


def format_reward_totals(totals: MutableMapping[str, float]) -> str:
    serialized = serialize_reward_totals(totals)
    if not serialized:
        return "$0.00"
    parts: list[str] = []
    for unit, value in serialized.items():
        if unit in {"$", "¥", "￥"}:
            if isinstance(value, int):
                parts.append(f"{unit}{value}")
            else:
                parts.append(f"{unit}{value:.4f}".rstrip("0").rstrip("."))
        elif unit == DEFAULT_REWARD_UNIT:
            parts.append(str(value))
        else:
            parts.append(f"{value} {unit}")
    return "、".join(parts)
