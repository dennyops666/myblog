#!/usr/bin/env python3
import requests
import re

# 设置会话以保持登录状态
session = requests.Session()

# 登录URL
login_url = "http://localhost:5000/auth/login"

# 先访问登录页面获取CSRF令牌(如果有的话)
print("正在访问登录页面...")
response = session.get(login_url)
print(f"登录页面状态码: {response.status_code}")

# 登录凭据
login_data = {
    "username": "admin",
    "password": "admin123",  # 基于密码检查结果，更改为正确的密码
    "remember_me": "y"
}

# 提交登录表单
print("正在登录...")
response = session.post(login_url, data=login_data)
print(f"登录提交状态码: {response.status_code}")
print(f"登录重定向: {response.url}")

# 检查是否登录成功
if "dashboard" in response.url or "admin" in response.url:
    print("登录成功!")
else:
    print("登录失败或意外的重定向")
    print("页面内容:")
    print(response.text[:500])  # 打印部分页面内容
    exit(1)

# 尝试访问用户创建页面
user_create_url = "http://localhost:5000/admin/user/create"
print(f"\n正在访问用户创建页面: {user_create_url}")
response = session.get(user_create_url)
print(f"状态码: {response.status_code}")

# 检查是否为200 OK
if response.status_code == 200:
    print("成功访问用户创建页面")
    
    # 检查页面是否包含创建用户的表单
    if "创建用户" in response.text and '<form method="post"' in response.text:
        print("页面中包含用户创建表单")
    else:
        print("页面中不包含预期的用户创建表单")
        print("页面内容:")
        print(response.text[:500])
elif response.status_code == 302:
    print(f"重定向到: {response.headers.get('Location')}")
else:
    print("访问失败")
    print("错误页面内容:")
    print(response.text[:500]) 