"""
飞书机器人推送服务
"""
import hmac
import hashlib
import base64
import time
import requests
import logging
from typing import Dict, Any

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("feishu")
class FeishuNotify(NotifyBase):
    """飞书机器人推送"""

    def _get_sign(self, timestamp: str) -> str:
        """生成签名"""
        secret = self.config.get("secret", "")
        if not secret:
            return ""

        string_to_sign = f'{timestamp}\n{secret}'
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        try:
            webhook = self.config.get("webhook")
            if not webhook:
                logger.error("飞书 webhook 未配置")
                return False

            timestamp = str(int(time.time()))

            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": "green" if "成功" in title else "red"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "plain_text",
                                "content": content
                            }
                        }
                    ]
                }
            }

            secret = self.config.get("secret")
            if secret:
                data["timestamp"] = timestamp
                data["sign"] = self._get_sign(timestamp)

            response = requests.post(webhook, json=data, timeout=10)
            result = response.json()

            if result.get("code") == 0 or result.get("StatusCode") == 0:
                logger.info("飞书推送成功")
                return True

            logger.error(f"飞书推送失败: {result.get('msg')}")
            return False

        except Exception as e:
            logger.error(f"飞书推送异常: {e}")
            return False

    def test(self) -> bool:
        return self.send("测试通知", "这是一条测试消息，来自 AnyRouter 管理平台。")
