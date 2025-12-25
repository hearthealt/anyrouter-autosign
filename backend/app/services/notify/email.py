"""
邮箱 SMTP 推送服务
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any

from .base import NotifyBase, NotifyFactory

logger = logging.getLogger(__name__)


@NotifyFactory.register("email")
class EmailNotify(NotifyBase):
    """邮箱 SMTP 推送"""

    def send(self, title: str, content: str, account_config: Dict[str, Any] = None) -> bool:
        to_email = account_config.get("to_email") if account_config else None
        if not to_email:
            logger.error("未提供收件人邮箱")
            return False

        try:
            smtp_host = self.config.get("smtp_host")
            smtp_port = int(self.config.get("smtp_port", 465))
            username = self.config.get("username")
            password = self.config.get("password")
            use_ssl = self.config.get("use_ssl", True)
            from_name = self.config.get("from_name", "AnyRouter")

            # 构建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = f"{from_name} <{username}>"
            msg["To"] = to_email

            # HTML 内容
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: {'#51cf66' if '成功' in title else '#ff6b6b'};">{title}</h2>
                <p style="color: #333; line-height: 1.6;">{content}</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">此邮件由 AnyRouter 管理平台自动发送</p>
            </body>
            </html>
            """

            msg.attach(MIMEText(content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            # 发送邮件
            if use_ssl:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                server.starttls()

            server.login(username, password)
            server.sendmail(username, [to_email], msg.as_string())
            server.quit()

            logger.info(f"邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"邮件发送异常: {e}")
            return False

    def test(self) -> bool:
        # 测试发送到自己
        username = self.config.get("username")
        return self.send(
            "测试通知",
            "这是一条测试消息，来自 AnyRouter 管理平台。",
            {"to_email": username}
        )
