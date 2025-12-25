"""
微信公众号推送服务
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("wechat_mp")
class WeChatMPNotify(NotifyBase):
    """微信公众号推送"""

    TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    MESSAGE_URL = "https://api.weixin.qq.com/cgi-bin/message/template/send"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token: Optional[str] = None

    def _get_access_token(self) -> bool:
        """获取访问令牌"""
        try:
            params = {
                "grant_type": "client_credential",
                "appid": self.config.get("app_id"),
                "secret": self.config.get("app_secret")
            }

            response = requests.get(self.TOKEN_URL, params=params, timeout=10)
            result = response.json()

            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                logger.error(f"获取微信令牌失败: {result.get('errmsg')}")
                return False

        except Exception as e:
            logger.error(f"获取微信令牌异常: {e}")
            return False

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        if not self.access_token and not self._get_access_token():
            return False

        openid = account_config.get("openid") if account_config else None
        if not openid:
            logger.error("未提供 OpenID")
            return False

        try:
            current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
            status = "成功" if "成功" in title else "失败"

            data = {
                "touser": openid,
                "template_id": self.config.get("template_id"),
                "data": {
                    "keyword1": {
                        "value": title,
                        "color": "#ff6b6b" if status == "失败" else "#51cf66"
                    },
                    "keyword2": {
                        "value": "AnyRouter签到",
                        "color": "#909399"
                    },
                    "keyword3": {
                        "value": current_time,
                        "color": "#909399"
                    },
                    "keyword4": {
                        "value": content,
                        "color": "#606266"
                    }
                }
            }

            url = f"{self.MESSAGE_URL}?access_token={self.access_token}"
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info("微信公众号推送成功")
                return True
            elif result.get("errcode") == 40001:
                # Token 过期，重新获取
                if self._get_access_token():
                    return self.send(title, content, account_config)

            logger.error(f"微信公众号推送失败: {result.get('errmsg')}")
            return False

        except Exception as e:
            logger.error(f"微信公众号推送异常: {e}")
            return False

    def test(self) -> bool:
        """测试推送 - 发送测试消息"""
        if not self._get_access_token():
            return False

        # 从配置中获取 openid
        openid = self.config.get("openid")
        if not openid:
            logger.error("测试失败: 未配置 OpenID")
            return False

        try:
            current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')

            data = {
                "touser": openid,
                "template_id": self.config.get("template_id"),
                "data": {
                    "keyword1": {
                        "value": "测试消息",
                        "color": "#51cf66"
                    },
                    "keyword2": {
                        "value": "AnyRouter签到",
                        "color": "#909399"
                    },
                    "keyword3": {
                        "value": current_time,
                        "color": "#909399"
                    },
                    "keyword4": {
                        "value": "这是一条测试消息，如果您收到此消息，说明微信公众号推送配置正确。",
                        "color": "#606266"
                    }
                }
            }

            url = f"{self.MESSAGE_URL}?access_token={self.access_token}"
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                logger.info("微信公众号测试推送成功")
                return True

            logger.error(f"微信公众号测试推送失败: {result.get('errmsg')}")
            return False

        except Exception as e:
            logger.error(f"微信公众号测试推送异常: {e}")
            return False
