import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import smtplib
from typing import Tuple

from config import SENDER_EMAIL, SENDER_PASSWORD
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from utils.logger_util import logger


class EmailUtil:
    sender_email = SENDER_EMAIL
    sender_password = SENDER_PASSWORD
    subject = "CourseQ&A 验证码"

    @staticmethod
    def send_email(receiver_email: str, code: str) -> Tuple[bool, str]:
        msg = MIMEMultipart()
        msg["From"] = EmailUtil.sender_email
        msg["To"] = receiver_email
        msg["Subject"] = EmailUtil.subject
        message = f"您的验证码为: {code}, 请妥善保管！验证码有效期为5分钟。"

        msg.attach(MIMEText(message, "plain"))
        try:
            server = smtplib.SMTP_SSL("smtp.163.com", 465)
            server.login(EmailUtil.sender_email, EmailUtil.sender_password)
            text = msg.as_string()
            server.sendmail(EmailUtil.sender_email, receiver_email, text)
            server.quit()
            logger.info("邮件发送成功！")
            return True, "success"
        except Exception as e:
            logger.error(f"邮件发送失败：{e}")
            return False, "验证码发送失败"


if __name__ == "__main__":
    email_sender = EmailUtil.send_email("3587655829@qq.com", "123456")

