"""
文件名：test_password_reset_simple.py
描述：简化的密码重置功能测试
作者：denny
"""

import pytest
from flask import url_for
from app.models import User
from app.utils.security import generate_token, verify_token

def test_reset_password_request_page(client):
    """测试重置密码请求页面"""
    response = client.get('/auth/reset_password_request')
    assert response.status_code == 200
    assert '重置密码'.encode('utf-8') in response.data

def test_reset_password_request_submit(client, init_test_users):
    """测试提交重置密码请求"""
    # 提交有效的邮箱
    response = client.post('/auth/reset_password_request', data={
        'email': 'admin@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert '重置密码链接已发送'.encode('utf-8') in response.data
    
    # 提交无效的邮箱
    response = client.post('/auth/reset_password_request', data={
        'email': 'nonexistent@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert '未找到该邮箱对应的用户'.encode('utf-8') in response.data

def test_reset_password_invalid_token(client):
    """测试无效的重置密码令牌"""
    # 访问重置密码页面，使用无效的令牌
    response = client.get('/auth/reset_password/invalid_token', follow_redirects=True)
    assert response.status_code == 200
    assert '无效或已过期的重置链接'.encode('utf-8') in response.data

def test_reset_password_valid_token(client, init_test_users, monkeypatch):
    """测试使用有效令牌重置密码"""
    # 模拟 verify_token 函数，使其返回有效的用户ID
    def mock_verify_token(token):
        if token == 'valid_token':
            return {'user_id': 1, 'action': 'reset_password'}
        return None
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 访问重置密码页面
    response = client.get('/auth/reset_password/valid_token')
    assert response.status_code == 200
    assert '重置密码'.encode('utf-8') in response.data
    
    # 提交重置密码表单
    response = client.post('/auth/reset_password/valid_token', data={
        'password': 'new_password123',
        'password2': 'new_password123',
        'token': 'valid_token'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert '密码已重置'.encode('utf-8') in response.data
    
    # 使用新密码登录
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'new_password123',
        'remember_me': False
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 检查是否登录成功
    assert '登录' not in response.data.decode('utf-8')

def test_reset_password_mismatch(client, init_test_users, monkeypatch):
    """测试密码不匹配的情况"""
    # 模拟 verify_token 函数，使其返回有效的用户ID
    def mock_verify_token(token):
        if token == 'valid_token':
            return {'user_id': 1, 'action': 'reset_password'}
        return None
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 提交重置密码表单，密码不匹配
    response = client.post('/auth/reset_password/valid_token', data={
        'password': 'new_password123',
        'password2': 'different_password',
        'token': 'valid_token'
    }, follow_redirects=False)
    
    # 表单验证失败，应该返回302状态码（重定向）
    assert response.status_code == 302
    
    # 检查重定向的位置是否为仪表盘页面
    assert '/dashboard/' in response.location 