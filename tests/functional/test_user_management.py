"""
文件名：test_user_management.py
描述：用户管理功能测试
作者：系统
"""

import os
import requests
from bs4 import BeautifulSoup
import re

# 测试配置
BASE_URL = 'http://192.168.72.128:5000'
USERNAME = 'admin'
PASSWORD = 'admin123'
NEW_USER = {
    'username': 'testuser',
    'email': 'test@example.com',
    'nickname': '测试用户',
    'password': 'Test123456',
    'password2': 'Test123456'
}

def login(session):
    """登录应用"""
    print(f"尝试访问登录页面: {BASE_URL}/auth/login")
    response = session.get(f'{BASE_URL}/auth/login')
    print(f"登录页面状态码: {response.status_code}")
    
    # 如果页面无法访问，打印详细信息
    if response.status_code != 200:
        print(f"无法访问登录页面! 响应代码: {response.status_code}")
        return False
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 获取登录表单的所有字段
    form_fields = {}
    for input_tag in soup.find_all('input'):
        name = input_tag.get('name')
        if name:
            form_fields[name] = input_tag.get('value', '')
    
    print(f"找到的表单字段: {list(form_fields.keys())}")
    
    # 登录表单提交
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
        'remember_me': 'y'
    }
    
    # 合并表单中可能存在的其他字段（如CSRF令牌）
    login_data.update({k: v for k, v in form_fields.items() if k not in login_data})
    
    print(f"提交登录表单: {BASE_URL}/auth/login")
    response = session.post(
        f'{BASE_URL}/auth/login',
        data=login_data,
        allow_redirects=True
    )
    
    print(f"登录响应状态码: {response.status_code}")
    print(f"登录后重定向到: {response.url}")
    
    # 检查登录状态
    if '/admin/' in response.url and response.status_code == 200:
        print("✓ 登录成功")
        return True
    else:
        print("✗ 登录失败")
        # 打印页面的一部分内容以帮助调试
        print(f"页面内容片段: {response.text[:500]}...")
        return False

def test_user_list():
    """测试用户列表页面"""
    with requests.Session() as session:
        if not login(session):
            return False
        
        # 访问用户列表页面
        response = session.get(f'{BASE_URL}/admin/user/')
        
        # 检查页面状态
        if response.status_code != 200:
            print(f"✗ 访问用户列表页面失败, 状态码: {response.status_code}")
            return False
        
        # 检查页面内容
        if '用户列表' in response.text and 'admin' in response.text:
            print("✓ 用户列表页面加载成功")
            return True
        else:
            print("✗ 用户列表页面内容不正确")
            return False

def test_create_user():
    """测试创建用户功能"""
    with requests.Session() as session:
        if not login(session):
            return False
        
        # 访问创建用户页面
        response = session.get(f'{BASE_URL}/admin/user/create')
        
        if response.status_code != 200:
            print(f"✗ 访问创建用户页面失败, 状态码: {response.status_code}")
            return False
        
        # 解析表单以获取CSRF令牌（如果有）
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = None
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input:
            csrf_token = csrf_input.get('value')
        
        # 准备创建用户的表单数据
        user_data = {
            'username': NEW_USER['username'],
            'email': NEW_USER['email'],
            'nickname': NEW_USER['nickname'],
            'password': NEW_USER['password'],
            'password2': NEW_USER['password2'],
            'is_active': 'y'
        }
        
        # 如果存在CSRF令牌，添加到表单数据中
        if csrf_token:
            user_data['csrf_token'] = csrf_token
        
        # 提交创建用户表单
        response = session.post(
            f'{BASE_URL}/admin/user/create',
            data=user_data,
            allow_redirects=True
        )
        
        # 检查重定向和创建结果
        if response.status_code != 200:
            print(f"✗ 创建用户提交失败, 状态码: {response.status_code}")
            return False
        
        # 检查是否有成功消息或新用户名
        if '用户创建成功' in response.text or NEW_USER['username'] in response.text:
            print("✓ 用户创建成功")
            
            # 访问用户列表页面检查新用户是否存在
            response = session.get(f'{BASE_URL}/admin/user/')
            if NEW_USER['username'] in response.text and NEW_USER['email'] in response.text:
                print("✓ 新用户已显示在用户列表中")
                return True
            else:
                print("✗ 新用户未显示在用户列表中")
                return False
        else:
            print("✗ 用户创建失败，未找到成功消息")
            print(f"页面内容片段: {response.text[:500]}...")
            return False

if __name__ == '__main__':
    print("\n运行用户管理功能测试...")
    print("\n1. 测试用户列表:")
    test_user_list()
    
    print("\n2. 测试创建用户:")
    test_create_user()
    
    print("\n测试完成!") 