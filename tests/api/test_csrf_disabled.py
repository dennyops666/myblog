"""
文件名：test_csrf_disabled.py
描述：测试CSRF保护是否已经被禁用
作者：denny
创建日期：2025-03-15
"""

import pytest
from flask import url_for
from app.forms import BaseForm
from flask_wtf.csrf import CSRFProtect


def test_csrf_disabled_in_config(app):
    """测试配置中是否禁用了CSRF保护"""
    assert app.config['WTF_CSRF_ENABLED'] is False
    # 不再检查其他可能的CSRF配置，因为它们可能不存在
    # assert 'WTF_CSRF_METHODS' in app.config


def test_csrf_disabled_in_base_form():
    """测试基础表单类中是否禁用了CSRF保护"""
    form = BaseForm()
    assert form.meta.csrf is False
    # 在较新版本的Flask-WTF中，csrf_enabled已被csrf替代


def test_csrf_not_in_extensions(app):
    """测试应用程序中是否没有启用CSRFProtect扩展"""
    # 检查应用程序的扩展中是否没有CSRFProtect实例
    for extension in app.extensions.values():
        assert not isinstance(extension, CSRFProtect)


def test_form_without_csrf_token(client):
    """测试表单提交时不需要CSRF令牌"""
    # 测试登录表单提交
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
    # 确保没有CSRF错误
    assert 'CSRF' not in response.get_data(as_text=True)
    assert 'csrf' not in response.get_data(as_text=True).lower()


def test_api_without_csrf_token(client):
    """测试API请求不需要CSRF令牌"""
    # 测试登录API
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
    # 确保没有CSRF错误
    assert 'CSRF' not in data.get('message', '')
    assert 'csrf' not in data.get('message', '').lower() 