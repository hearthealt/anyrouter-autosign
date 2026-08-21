"""签到适配器公共接口。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol, Tuple

from sqlalchemy.orm import Session

from app.models import Account


@dataclass(frozen=True)
class AdapterCapabilities:
    """用于 API 和前端决定哪些能力可用。"""

    requires_external_user_id: bool = False
    supports_user_info: bool = False
    supports_tokens: bool = False
    supports_models: bool = False
    supports_groups: bool = False
    supports_health_check: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return {
            "requires_external_user_id": self.requires_external_user_id,
            "supports_user_info": self.supports_user_info,
            "supports_tokens": self.supports_tokens,
            "supports_models": self.supports_models,
            "supports_groups": self.supports_groups,
            "supports_health_check": self.supports_health_check,
        }


class PlatformAdapter(Protocol):
    """所有签到平台适配器都必须实现的最小协议。"""

    adapter_type: str
    capabilities: AdapterCapabilities

    def sign(
        self,
        db: Session,
        account: Account,
        platform_config: Dict[str, Any],
    ) -> Tuple[bool, Dict[str, Any]]:
        """执行一次签到并返回 (请求是否完成, 统一结果)。"""
        ...
