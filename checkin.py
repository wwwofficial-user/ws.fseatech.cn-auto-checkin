#!/usr/bin/env python3
"""
网站自动签到脚本 - v1.1
需要设置的 GitHub Secrets:
- EMAIL: 登录邮箱
- PASSWORD: 登录密码
- MAIL_FROM: 发件邮箱
- MAIL_PASSWORD: 发件邮箱授权码
- MAIL_TO: 收件邮箱
(CSRF_TOKEN 现在从网站获取，不需要手动设置)
"""

import os
import requests
import json
import smtplib
import re
import hashlib
import time
import uuid
from email.mime.text import MIMEText
from email.header import Header
from datetime import datetime
from typing import Optional, Dict, Any
import sys

# 网站配置
BASE_URL = "https://ws.fseatech.cn"
LOGIN_URL = f"{BASE_URL}/api/user/login"
CHECKIN_URL = f"{BASE_URL}/api/points/checkin"
INDEX_URL = BASE_URL  # 🤔用于获取csrf_token

# 请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=1,i"
}

class CSRFManager:
    """管理CSRF token，可以生成、存储和使用"""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """生成一个随机的CSRF token，模拟浏览器行为"""
        # 使用时间戳和随机UUID生成
        timestamp = int(time.time() * 1000)
        unique_id = str(uuid.uuid4()).replace('-', '')
        
        # 生成类似抓包中的token格式
        token_data = f"{timestamp}{unique_id}"
        csrf_token = hashlib.sha256(token_data.encode()).hexdigest()
        
        print(f"生成新的CSRF token: {csrf_token[:16]}...")
        return csrf_token
    
    @staticmethod
    def get_csrf_token_from_site() -> Optional[str]:
        """从网站首页获取CSRF token"""
        try:
            print("尝试从网站获取CSRF token...")
            response = requests.get(
                INDEX_URL,
                headers=HEADERS,
                timeout=30
            )
            
            if response.status_code == 200:
                # 方法1: 从Set-Cookie头获取
                cookies = response.cookies.get_dict()
                if 'csrf_token' in cookies:
                    csrf_token = cookies['csrf_token']
                    print(f"从Cookie获取到CSRF token: {csrf_token[:16]}...")
                    return csrf_token
                
                # 方法2: 从HTML中查找（如果网站有的话）
                html_content = response.text
                # 查找常见的CSRF token位置
                patterns = [
                    r'name="csrf_token" value="([^"]+)"',
                    r'csrf_token["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                    r'X-CSRF-Token["\']?\s*[:=]\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.search(pattern, html_content)
                    if matches:
                        csrf_token = matches.group(1)
                        print(f"从HTML获取到CSRF token: {csrf_token[:16]}...")
                        return csrf_token
                
                print("网站未返回CSRF token，将使用生成的token")
                return None
            else:
                print(f"访问网站失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"获取CSRF token时出错: {e}")
            return None

class CheckinBot:
    """签到机器人"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.csrf_token = None
        self.auth_token = None
        
    def get_env_variable(self, name: str, required: bool = True) -> Optional[str]:
        """从环境变量获取配置"""
        value = os.environ.get(name)
        if required and not value:
            print(f"错误: 环境变量 {name} 未设置")
            return None
        return value
    
    def init_csrf_token(self) -> bool:
        """初始化CSRF token"""
        # 尝试从网站获取
        csrf_token = CSRFManager.get_csrf_token_from_site()
        
        if csrf_token:
            self.csrf_token = csrf_token
        else:
            # 生成一个token备用
            self.csrf_token = CSRFManager.generate_csrf_token()
        
        # 设置cookie
        self.session.cookies.set('csrf_token', self.csrf_token)
        print(f"使用CSRF token: {self.csrf_token[:16]}...")
        return True
    
    def login(self) -> bool:
        """登录网站"""
        email = self.get_env_variable("EMAIL")
        password = self.get_env_variable("PASSWORD")
        
        if not email or not password:
            return False
        
        login_data = {
            "email": email,
            "password": password
        }
        
        # 设置请求头
        headers = HEADERS.copy()
        headers["Content-Type"] = "application/json"
        headers["Referer"] = f"{BASE_URL}/login"
        headers["Origin"] = BASE_URL
        
        try:
            print(f"正在登录账号: {email}")
            response = self.session.post(
                LOGIN_URL,
                headers=headers,
                json=login_data,
                timeout=30
            )
            
            print(f"登录响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"登录响应: {json.dumps(result, ensure_ascii=False)}")
                
                if result.get("code") == 0:
                    self.auth_token = result.get("data", {}).get("token")
                    if self.auth_token:
                        print("登录成功，获取到token")
                        return True
                    else:
                        print("登录成功但未获取到token")
                else:
                    print(f"登录失败: {result.get('message')}")
            else:
                print(f"登录请求失败: {response.status_code}, {response.text[:200]}")
                
        except Exception as e:
            print(f"登录过程中发生错误: {e}")
        
        return False
    
    def checkin(self) -> Dict[str, Any]:
        """执行签到"""
        if not self.auth_token:
            return {"error": "未登录"}
        
        headers = HEADERS.copy()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {self.auth_token}"
        headers["Referer"] = f"{BASE_URL}/my/checkin"
        headers["Origin"] = BASE_URL
        
        try:
            print("正在执行签到...")
            response = self.session.post(
                CHECKIN_URL,
                headers=headers,
                timeout=30
            )
            
            print(f"签到响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"签到响应: {json.dumps(result, ensure_ascii=False)}")
                return result
            else:
                print(f"签到请求失败: {response.status_code}, {response.text[:200]}")
                return {"error": f"HTTP {response.status_code}", "message": response.text[:200]}
                
        except Exception as e:
            print(f"签到过程中发生错误: {e}")
            return {"error": str(e)}
    
    def run(self) -> bool:
        """执行完整的签到流程"""
        print("=" * 60)
        print(f"自动签到开始 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 初始化CSRF token
        if not self.init_csrf_token():
            print("初始化CSRF token失败")
            return False
        
        # 2. 登录
        if not self.login():
            print("登录失败")
            return False
        
        # 3. 签到
        result = self.checkin()
        
        # 4. 生成结果报告
        self.generate_report(result)
        
        print("=" * 60)
        print("自动签到完成")
        print("=" * 60)
        
        return "error" not in result
    
    def generate_report(self, result: Dict[str, Any]) -> str:
        """生成报告并发送邮件"""
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if "error" in result:
            # 签到失败
            subject = "自动签到失败"
            content = f"""❌ 签到失败
时间: {current_time}
错误: {result.get('error', '未知错误')}
详细信息: {result.get('message', '无')}
"""
        else:
            code = result.get("code", -999)
            message = result.get("message", "未知状态")
            data = result.get("data", {})
            
            if code == 0:
                # 签到成功
                subject = "自动签到成功"
                coupon_reward = data.get('couponReward', False)
                coupon_count = 1 if coupon_reward else 0    
                content = f"""✅ 签到成功！
时间: {current_time}
状态: {message}
本次积分: {data.get('pointsEarned', 'N/A')}
总积分: {data.get('totalPoints', 'N/A')}
连续天数: {data.get('consecutiveDays', 'N/A')}
签名卷: 获得{coupon_count}张
"""
            elif code == -1 and "今日已签到" in message:
                # 已签到
                subject = "自动签到提醒 - 今日已签到"
                coupon_reward = data.get('couponReward', False)
                coupon_count = 1 if coupon_reward else 0    
                content = f"""ℹ️ 今日已签到
时间: {current_time}
状态: {message}
本次积分: {data.get('pointsEarned', 'N/A')}
总积分: {data.get('totalPoints', 'N/A')}
连续天数: {data.get('consecutiveDays', 'N/A')}
签名卷: 获得{coupon_count}张
"""
            else:
                # 其他情况
                subject = "自动签到异常"
                content = f"""⚠️ 签到异常
时间: {current_time}
返回代码: {code}
信息: {message}
数据: {json.dumps(data, ensure_ascii=False, indent=2)}
"""
        
        print("\n" + "=" * 40)
        print("签到结果:")
        print(content)
        print("=" * 40)
        
        # 发送邮件
        self.send_email(subject, content)
        
        return content
    
    def send_email(self, subject: str, content: str) -> bool:
        """发送邮件通知"""
        try:
            mail_from = self.get_env_variable("MAIL_FROM")
            mail_password = self.get_env_variable("MAIL_PASSWORD")
            mail_to = self.get_env_variable("MAIL_TO")
            
            if not mail_from or not mail_password or not mail_to:
                print("邮件配置不完整，跳过发送邮件")
                return False
            
            # 根据邮箱自动选择SMTP服务器
            mail_host_map = {
                "qq.com": ("smtp.qq.com", 465),
                "163.com": ("smtp.163.com", 465),
                "126.com": ("smtp.126.com", 465),
                "gmail.com": ("smtp.gmail.com", 465),
                "outlook.com": ("smtp.office365.com", 587),
                "hotmail.com": ("smtp.office365.com", 587)
            }
            
            # 提取邮箱域名
            mail_domain = mail_from.split('@')[-1]
            smtp_server, smtp_port = mail_host_map.get(mail_domain, ("smtp.qq.com", 465))
            
            print(f"使用 {smtp_server}:{smtp_port} 发送邮件")
            
            # 创建邮件
            msg = MIMEText(content, 'plain', 'utf-8')
            msg['From'] = Header(f"自动签到机器人 <{mail_from}>")
            msg['To'] = Header(f"<{mail_to}>")
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 发送邮件
            if smtp_port == 587:
                # 需要TLS
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(mail_from, mail_password)
                    server.sendmail(mail_from, [mail_to], msg.as_string())
            else:
                # SSL
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(mail_from, mail_password)
                    server.sendmail(mail_from, [mail_to], msg.as_string())
            
            print("邮件发送成功")
            return True
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False #👿👿👿认证失败

def main():
    """主函数"""
    bot = CheckinBot()
    success = bot.run()
    
    if not success:
        print("签到流程执行失败")
        sys.exit(1)    
if __name__ == "__main__":
    main()       