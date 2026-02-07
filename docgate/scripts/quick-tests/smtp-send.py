import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from docgate.config import SMTP_CONF

g_receiver_email = "readonlyfile@hotmail.com"


def naive():
  subject = "Test Email from Python"
  body = "This is a test email sent using Python's smtplib."
  # 创建 MIMEMultipart 对象，并附加邮件主题和正文
  message = MIMEMultipart()
  message["From"] = SMTP_CONF.account_email
  message["To"] = g_receiver_email
  message["Subject"] = subject
  message.attach(MIMEText(body, "plain"))

  # 连接到 SMTP 服务器并发送邮件
  try:
    # 使用 SSL 连接到邮件服务器
    with smtplib.SMTP_SSL(SMTP_CONF.host, SMTP_CONF.port) as server:
      server.login(SMTP_CONF.account_email, SMTP_CONF.account_password)  # 登录 SMTP 服务器
      text = message.as_string()  # 将邮件内容转换为字符串
      server.sendmail(SMTP_CONF.account_email, g_receiver_email, text)  # 发送邮件
      print("邮件发送成功")
  except Exception as e:
    print(f"邮件发送失败: {e}")
    raise


async def supertokens_impl():
  from supertokens_python.ingredients.emaildelivery.types import EmailContent
  from supertokens_python.recipe import emailpassword

  from docgate.supertokens_config import _get_smtp_settings, init_supertokens

  init_supertokens()

  smtp_service = emailpassword.SMTPService(smtp_settings=_get_smtp_settings())
  content = EmailContent(
    body="Test chinese name email",
    subject="Used to test supertokens send email",
    to_email=g_receiver_email,
    is_html=True,
  )
  print("SEND by smtp async smtp service")
  await smtp_service.service_implementation.transporter.send_email(content, {})
  print("DONE")


if __name__ == "__main__":
  # naive()
  import asyncio

  asyncio.run(supertokens_impl())
