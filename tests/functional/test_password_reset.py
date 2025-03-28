"""
文件名：test_password_reset.py
描述：密码重置功能测试
作者：denny
"""

import pytest
from flask import url_for
from app.models import User
from app.extensions import db
from app.utils.security import generate_token

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

def test_reset_password_page(client, init_test_users, monkeypatch):
    """测试重置密码页面"""
    # 模拟 verify_token 函数，使其返回有效的用户ID
    def mock_verify_token(token):
        return {'user_id': 1, 'action': 'reset_password'}
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 访问重置密码页面，添加 follow_redirects=True
    response = client.get('/auth/reset_password/mock_token', follow_redirects=True)
    assert response.status_code == 200
    assert '重置密码'.encode('utf-8') in response.data

def test_reset_password_submit(client, init_test_users, monkeypatch):
    """测试提交重置密码"""
    # 模拟 verify_token 函数，使其返回有效的用户ID
    def mock_verify_token(token):
        return {'user_id': 1, 'action': 'reset_password'}
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 提交重置密码表单
    response = client.post('/auth/reset_password/mock_token', data={
        'password': 'new_password123',
        'password2': 'new_password123',
        'token': 'mock_token'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert '密码已重置'.encode('utf-8') in response.data

def test_reset_password_invalid_token(client):
    """测试无效的重置密码令牌"""
    # 访问重置密码页面，使用无效的令牌
    response = client.get('/auth/reset_password/invalid_token', follow_redirects=True)
    assert response.status_code == 200
    assert '无效或已过期的重置链接'.encode('utf-8') in response.data
    
    # 提交重置密码表单，使用无效的令牌
    response = client.post('/auth/reset_password/invalid_token', data={
        'password': 'new_password123',
        'password2': 'new_password123',
        'token': 'invalid_token'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert '无效或已过期的重置链接'.encode('utf-8') in response.data

def test_reset_password_mismatch(client, init_test_users, monkeypatch):
    """测试重置密码不匹配"""
    # 模拟 verify_token 函数，使其返回有效的用户ID
    def mock_verify_token(token):
        return {'user_id': 1, 'action': 'reset_password'}
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 提交重置密码表单，密码不匹配
    response = client.post('/auth/reset_password/mock_token', data={
        'password': 'new_password123',
        'password2': 'different_password',
        'token': 'mock_token'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert '两次输入的密码不一致'.encode('utf-8') in response.data

def test_reset_password_nonexistent_user(client, monkeypatch):
    """测试不存在的用户"""
    # 模拟 verify_token 函数，使其返回不存在的用户ID
    def mock_verify_token(token):
        return {'user_id': 999, 'action': 'reset_password'}
    
    # 应用模拟
    monkeypatch.setattr('app.views.auth.verify_token', mock_verify_token)
    
    # 访问重置密码页面
    response = client.get('/auth/reset_password/mock_token', follow_redirects=True)
    assert response.status_code == 200
    assert '用户不存在'.encode('utf-8') in response.data 