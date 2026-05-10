import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 获取GitHub secrets注入的环境变量
COOKIE = os.getenv('WS_COOKIE')
MAIL_USER = os.getenv('MAIL_USER')
MAIL_PASS = os.getenv('MAIL_PASS')
TO_MAIL = os.getenv('TO_MAIL')

# 签到😈
sign_url = "http://ws.fseatech.cn/api/points/"
headers = {
    'Cookie': COOKIE,
    'User-Agent': 'Mozilla/5.0'
}

try:
    response = requests.post(sign_url, headers=headers, timeout=15)
    sign_result = response.text
    success = response.status_code == 200 and ('success' in sign_result or '成功' in sign_result)
except Exception as e:
    sign_result = f"签到出错:{str(e)}"
    success = False

# 拼接标题内容
subject = 'FSeaTech签到成功' if success else 'FSeaTech签到失败'
content = f"""签到接口URL: {sign_url}
请求头: {headers}
签到接口响应内容:
{sign_result}
"""

# 邮件发送逻辑，Outlook smtp配置
def send_email(subject, content):
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = Header(MAIL_USER)
    msg['To'] = Header(TO_MAIL)
    msg['Subject'] = Header(subject)
    
    try:
        # Outlook SMTP
        smtp = smtplib.SMTP('smtp.office365.com', 587)
        smtp.starttls()
        smtp.login(MAIL_USER, MAIL_PASS)
        smtp.sendmail(MAIL_USER, [TO_MAIL], msg.as_string())
        smtp.quit()
        print('邮件发送成功')
    except Exception as e:
        print('邮件发送失败:', e)

# 调用发送邮件函数
send_email(subject, content)

