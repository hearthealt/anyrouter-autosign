"""
推送服务
"""
from .email import EmailNotify
from .base import NotifyBase, NotifyFactory
from .pushplus import PushPlusNotify
from .wechat_mp import WeChatMPNotify
from .wechat_work import WeChatWorkNotify
from .dingtalk import DingTalkNotify
from .feishu import FeishuNotify

__all__ = [
    "NotifyBase",
    "NotifyFactory",
    "PushPlusNotify",
    "WeChatMPNotify",
    "WeChatWorkNotify",
    "DingTalkNotify",
    "FeishuNotify",
    "EmailNotify"
]
