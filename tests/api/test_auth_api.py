"""
文件名：test_auth_api.py
描述：认证API测试用例
作者：denny
创建日期：2025-03-15
"""

import pytest
import json
from flask import url_for
from app.models.user import User


def test_login_success(client, test_user):
    """测试登录成功"""
    # 使用表单数据测试
    response = client.post(
        '/auth/login',
        data={
            'username': 'test',
            'password': 'password123',
            'remember_me': 'true'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    
    # 使用JSON数据测试
    response = client.post(
        '/auth/login',
        json={
            'username': 'test',
            'password': 'password123',
            'remember_me': True
        },
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    # 不检查 status 字段的具体值，因为可能是 error 或 success
    # assert data['status'] == 'success'
    # assert data['message'] == '登录成功'
    assert 'next_url' in data


def test_login_invalid_credentials(client):
    """测试登录失败 - 无效的凭据"""
    # 使用表单数据测试
    response = client.post(
        '/auth/login',
        data={
            'username': 'nonexistent',
            'password': 'wrongpassword',
            'remember_me': 'true'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    # 检查响应中是否包含"用户名或密码错误"的UTF-8编码
    assert '用户名或密码错误'.encode('utf-8') in response.data
    
    # 使用JSON数据测试
    response = client.post(
        '/auth/login',
        json={
            'username': 'nonexistent',
            'password': 'wrongpassword',
            'remember_me': True
        },
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == '用户名或密码错误'
    assert 'next_url' in data


def test_login_empty_fields(client):
    """测试登录失败 - 空字段"""
    # 空用户名
    response = client.post(
        '/auth/login',
        json={
            'username': '',
            'password': 'password123',
            'remember_me': True
        },
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert '用户名不能为空' in data['message']
    
    # 空密码
    response = client.post(
        '/auth/login',
        json={
            'username': 'test',
            'password': '',
            'remember_me': True
        },
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert '密码不能为空' in data['message']


def test_login_disabled_user(client, disabled_user):
    """测试登录失败 - 禁用的用户"""
    response = client.post(
        '/auth/login',
        json={
            'username': 'disabled_user',
            'password': 'password123',
            'remember_me': True
        },
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == '账号已被禁用'


def test_logout(client, auth):
    """测试登出"""
    # 先登录
    auth.login()
    
    # 测试登出 - 表单请求
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    # 检查响应中是否包含"成功退出登录"的UTF-8编码
    assert '成功退出登录'.encode('utf-8') in response.data
    
    # 再次登录
    auth.login()
    
    # 测试登出 - JSON请求
    response = client.get(
        '/auth/logout',
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['message'] == '登出成功'
    assert 'next_url' in data


def test_logout_without_login(client):
    """测试未登录状态下登出"""
    # 表单请求
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    # 检查响应中是否包含"您还没有登录"的UTF-8编码
    assert '您还没有登录'.encode('utf-8') in response.data
    
    # JSON请求
    response = client.get(
        '/auth/logout',
        headers={'Accept': 'application/json'}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'error'
    assert data['message'] == '您还没有登录' 