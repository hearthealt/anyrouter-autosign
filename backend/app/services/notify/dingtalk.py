"""
钉钉机器人推送服务
"""
import hmac
import hashlib
import base64
import time
import urllib.parse
import requests
import logging
from typing import Dict, Any

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("dingtalk")
class DingTalkNotify(NotifyBase):
    """钉钉机器人推送"""

    def _get_sign(self) -> str:
        """生成签名"""
        secret = self.config.get("secret", "")
        if not secret:
            return ""

        timestamp = str(round(time.time() * 1000))
        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        return f"&timestamp={timestamp}&sign={sign}"

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        try:
            webhook = self.config.get("webhook")
            if not webhook:
                logger.error("钉钉 webhook 未配置")
                return False

            url = webhook + self._get_sign()

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"## {title}\n\n{content}"
                }
            }

            # 处理 @ 指定人
            if account_config and account_config.get("at_mobiles"):
                data["at"] = {
                    "atMobiles": account_config["at_mobiles"],
                    "isAtAll": False
                }

            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info("钉钉推送成功")
                return True

            logger.error(f"钉钉推送失败: {result.get('errmsg')}")
            return False

        except Exception as e:
            logger.error(f"钉钉推送异常: {e}")
            return False

    def test(self) -> bool:
        return self.send("测试通知", "这是一条测试消息，来自 AnyRouter 管理平台。")
