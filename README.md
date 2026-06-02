# ws.fseatech.cn-auto-checkin
A GitHub action for automated check-ins
about：https://ws.fseatech.cn/
# 网站自动签到脚本 - v1.2

## 主要改进
1. **自动处理CSRF token**：无需手动设置CSRF_TOKEN
2. **更智能的错误处理**：更好的日志和错误报告
3. **自动识别邮箱服务商**：自动选择正确的SMTP服务器
4. **增强的报告功能**：更详细的签到结果报告

## 设置步骤

### 1. 配置 GitHub Secrets
只需要设置以下4个Secrets：

1. **EMAIL**: 您的登录邮箱
2. **PASSWORD**: 您的登录密码
3. **MAIL_FROM**: 发件邮箱地址
4. **MAIL_PASSWORD**: 发件邮箱授权码
5. **MAIL_TO**: 收件邮箱地址

### 2. 邮箱配置说明
脚本支持以下邮箱服务商：
- QQ邮箱 (qq.com)
- 163邮箱 (163.com)
- 126邮箱 (126.com)
- Gmail (gmail.com)
- Outlook/Hotmail (outlook.com/hotmail.com)

其他邮箱需要手动修改SMTP服务器配置。

### 3. CSRF Token 处理
脚本会自动：
1. 尝试从网站获取CSRF token
2. 如果获取失败，会生成一个合法的token
3. 使用这个token进行登录和签到

Some issues cannot be run.

That's all.