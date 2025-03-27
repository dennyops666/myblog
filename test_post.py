#!/usr/bin/env python3
import requests

print("开始测试用户创建...")

url = "http://localhost:5000/admin/user/create"

# 先获取表单页面
session = requests.Session()
response = session.get(url)

if response.status_code == 200:
    print("成功获取表单页面")
else:
    print(f"获取表单页面失败，状态码: {response.status_code}")
    exit(1)

# 创建测试用户数据
data = {
    "username": "test-script-user",
    "email": "test-script@example.com",
    "nickname": "测试脚本用户",
    "password": "Test@12345",
    "password2": "Test@12345",
    "roles": "4",  # editor角色ID
    "is_active": "on"
}

# 提交表单
print("提交表单数据...")
response = session.post(url, data=data)

# 打印结果
print(f"响应状态码: {response.status_code}")
print(f"响应头部: {response.headers}")
print(f"重定向URL: {response.url}" if response.history else "无重定向")

# 检查结果
if response.status_code == 200 or response.status_code == 302:
    if "成功" in response.text:
        print("用户创建成功!")
    elif "失败" in response.text:
        print("用户创建失败!")
        print("错误信息:", response.text[:500])
    else:
        print("未能确定结果，请检查应用日志")
else:
    print("请求失败，请检查应用日志") 