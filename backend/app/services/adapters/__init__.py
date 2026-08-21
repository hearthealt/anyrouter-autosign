"""内置签到适配器。"""
from app.services.adapters.base import AdapterCapabilities, PlatformAdapter
from app.services.adapters.configurable_http import ConfigurableHttpAdapter
from app.services.adapters.new_api import NewApiAdapter
from app.services.adapters.registry import AdapterRegistry, adapter_registry

adapter_registry.register(NewApiAdapter())
adapter_registry.register(ConfigurableHttpAdapter())

__all__ = [
    "AdapterCapabilities",
    "PlatformAdapter",
    "AdapterRegistry",
    "adapter_registry",
    "NewApiAdapter",
    "ConfigurableHttpAdapter",
]
