"""
PushPlus 推送服务
"""
import requests
import logging
from typing import Dict, Any

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("pushplus")
class PushPlusNotify(NotifyBase):
    """PushPlus 推送"""

    API_URL = "http://www.pushplus.plus/send"

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        try:
            data = {
                "token": self.config.get("token"),
                "title": title,
                "content": content,
                "template": "html"
            }

            topic = self.config.get("topic")
            if topic:
                data["topic"] = topic

            response = requests.post(self.API_URL, json=data, timeout=10)
            result = response.json()

            if result.get("code") == 200:
                logger.info("PushPlus 推送成功")
                return True
            else:
                logger.error(f"PushPlus 推送失败: {result.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"PushPlus 推送异常: {e}")
            return False

    def test(self) -> bool:
        return self.send("测试通知", "这是一条测试消息，来自 AnyRouter 管理平台。")
