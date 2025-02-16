"""
文件名：test_security.py
描述：安全性测试
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.utils.markdown import markdown_to_html

def test_markdown_xss_protection():
    """测试Markdown XSS防护"""
    # 测试脚本注入
    markdown_content = """
# 标题

<script>alert('xss')</script>

[链接](javascript:alert('xss'))

<img src="x" onerror="alert('xss')">
"""
    result = markdown_to_html(markdown_content)
    html = result['html']
    
    # 验证脚本标签被移除
    assert '<script>' not in html
    assert 'alert' not in html
    
    # 验证javascript链接被移除
    assert 'javascript:' not in html
    
    # 验证危险属性被移除
    assert 'onerror' not in html

def test_comment_xss_protection(client, test_post):
    """测试评论XSS防护"""
    # 尝试提交包含XSS的评论
    response = client.post(
        f'/post/{test_post.id}/comment',
        data={
            'author_name': '<script>alert("xss")</script>',
            'author_email': 'test@example.com',
            'content': '<img src="x" onerror="alert(\'xss\')">'
        }
    )
    
    # 验证评论页面
    response = client.get(f'/post/{test_post.id}')
    assert '<script>' not in response.data.decode()
    assert 'onerror' not in response.data.decode()

def test_csrf_protection(client):
    """测试CSRF防护"""
    # 测试不带CSRF令牌的POST请求
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 400  # 请求应被拒绝
    
    # 获取登录页面的CSRF令牌
    response = client.get('/auth/login')
    assert 'csrf_token' in response.data.decode()

def test_password_security(test_user):
    """测试密码安全性"""
    # 验证密码已加密存储
    assert test_user.password_hash != 'password'
    assert len(test_user.password_hash) > 20
    
    # 验证原始密码无法访问
    with pytest.raises(AttributeError):
        _ = test_user.password
    
    # 验证密码验证功能
    assert test_user.verify_password('password')
    assert not test_user.verify_password('wrong_password')

def test_session_security(client, auth):
    """测试会话安全性"""
    # 登录
    auth.login()
    
    # 验证会话cookie
    with client.session_transaction() as session:
        assert '_user_id' in session
        assert session.permanent is True  # 会话持久化
        
    # 登出
    auth.logout()
    with client.session_transaction() as session:
        assert '_user_id' not in session

def test_sql_injection_prevention(client):
    """测试SQL注入防护"""
    # 尝试SQL注入登录
    response = client.post('/auth/login', data={
        'username': "admin' OR '1'='1",
        'password': "' OR '1'='1"
    })
    assert response.status_code in (401, 403)  # 登录应失败
    
    # 尝试SQL注入搜索
    response = client.get('/search?q=1%27%20OR%20%271%27=%271')
    assert response.status_code == 200  # 页面应正常加载
    # 验证没有泄露数据库错误信息
    assert 'SQL' not in response.data.decode()
    assert 'database' not in response.data.decode().lower()