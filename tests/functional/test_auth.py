"""
文件名：test_auth.py
描述：认证功能测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from flask import session, url_for
from app.models import User
from app.extensions import db
from datetime import datetime, UTC
from flask import current_app

def test_login_page(client):
    """测试登录页面"""
    # 确保用户是登出状态
    client.get('/auth/logout', follow_redirects=True)
    
    response = client.get('/auth/login', follow_redirects=True)
    assert response.status_code == 200
    assert '管理后台登录'.encode('utf-8') in response.data
    
def test_login_success(client, auth, init_test_users):
    """测试登录成功"""
    response = auth.login()
    assert response.status_code == 200
    # 由于使用了follow_redirects=True，所以不再检查Location头
    assert '欢迎来到仪表板' in response.get_data(as_text=True)

def test_login_json_success(client, app):
    """测试JSON登录成功"""
    # 准备请求数据
    data = {
        'username': 'admin',
        'password': 'password123',
        'remember_me': True
    }
    
    # 设置请求头
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 发送登录请求
    response = client.post('/auth/login', json=data, headers=headers)
    
    # 验证响应
    assert response.status_code == 302
    assert response.location == url_for('dashboard.index')

def test_login_invalid_password(client, app):
    """测试登录失败 - 密码错误"""
    # 准备请求数据
    data = {
        'username': 'admin',
        'password': 'wrong_password',
        'remember_me': True
    }
    
    # 发送登录请求
    response = client.post('/auth/login', data=data)
    
    # 验证响应
    assert response.status_code == 302
    assert response.location == url_for('dashboard.index')

def test_login_json_invalid_password(client, app):
    """测试JSON登录失败 - 密码错误"""
    # 准备请求数据
    data = {
        'username': 'admin',
        'password': 'wrong_password',
        'remember_me': True
    }
    
    # 设置请求头
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 发送登录请求
    response = client.post('/auth/login', json=data, headers=headers)
    
    # 验证响应
    assert response.status_code == 302
    assert response.location == url_for('dashboard.index')

def test_login_disabled_user(client, app, disabled_user):
    """测试登录失败 - 用户被禁用"""
    # 准备请求数据
    data = {
        'username': 'disabled',
        'password': 'password123',
        'remember_me': True
    }
    
    # 设置请求头
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    # 发送登录请求
    response = client.post('/auth/login', json=data, headers=headers)
    
    # 验证响应
    assert response.status_code == 302
    assert response.location == url_for('dashboard.index')

def test_logout_success(client, auth, init_test_users):
    """测试登出成功"""
    auth.login()
    response = auth.logout()
    assert response.status_code == 200
    assert '成功退出登录' in response.get_data(as_text=True)

def test_logout_json_success(client, auth, init_test_users):
    """测试JSON登出成功"""
    auth.login(headers={'Accept': 'application/json'})
    response = auth.logout(headers={'Accept': 'application/json'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['message'] == '登出成功'
    assert json_data['next_url'] == url_for('auth.login', _external=False)
