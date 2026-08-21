"""适配器注册表。"""
from __future__ import annotations

from typing import Dict, Iterable

from app.services.adapters.base import PlatformAdapter


class AdapterRegistry:
    def __init__(self) -> None:
        self._adapters: Dict[str, PlatformAdapter] = {}

    def register(self, adapter: PlatformAdapter) -> None:
        adapter_type = adapter.adapter_type.strip().lower()
        if not adapter_type:
            raise ValueError("adapter_type 不能为空")
        self._adapters[adapter_type] = adapter

    def get(self, adapter_type: str) -> PlatformAdapter:
        normalized = (adapter_type or "").strip().lower()
        adapter = self._adapters.get(normalized)
        if adapter is None:
            raise ValueError(f"未注册的平台适配器: {normalized or '<empty>'}")
        return adapter

    def values(self) -> Iterable[PlatformAdapter]:
        return self._adapters.values()


adapter_registry = AdapterRegistry()
