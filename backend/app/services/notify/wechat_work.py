"""
企业微信推送服务
"""
import requests
import logging
from typing import Dict, Any, Optional

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("wechat_work")
class WeChatWorkNotify(NotifyBase):
    """企业微信推送"""

    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    MESSAGE_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token: Optional[str] = None

    def _get_access_token(self) -> bool:
        """获取访问令牌"""
        try:
            params = {
                "corpid": self.config.get("corp_id"),
                "corpsecret": self.config.get("corp_secret")
            }

            response = requests.get(self.TOKEN_URL, params=params, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                self.access_token = result["access_token"]
                return True
            else:
                logger.error(f"获取企业微信令牌失败: {result.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"获取企业微信令牌异常: {e}")
            return False

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        if not self.access_token and not self._get_access_token():
            return False

        try:
            user_id = "@all"
            if account_config and account_config.get("user_id"):
                user_id = account_config["user_id"]

            data = {
                "touser": user_id,
                "msgtype": "text",
                "agentid": int(self.config.get("agent_id", 0)),
                "text": {
                    "content": f"{title}\n\n{content}"
                }
            }

            url = f"{self.MESSAGE_URL}?access_token={self.access_token}"
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info("企业微信推送成功")
                return True

            logger.error(f"企业微信推送失败: {result.get('errmsg')}")
            return False

        except Exception as e:
            logger.error(f"企业微信推送异常: {e}")
            return False

    def test(self) -> bool:
        return self.send("测试通知", "这是一条测试消息，来自 AnyRouter 管理平台。")
