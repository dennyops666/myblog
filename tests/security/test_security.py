"""
文件名：test_security.py
描述：安全性测试用例
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.utils.markdown import markdown_to_html

def test_markdown_xss_protection(app_context):
    """测试Markdown XSS防护"""
    # 测试包含恶意脚本的Markdown
    malicious_content = """
# 标题

<script>alert('xss')</script>

[链接](javascript:alert('xss'))

<img src="x" onerror="alert('xss')">

```html
<script>alert('xss')</script>
```
"""
    
    result = markdown_to_html(malicious_content)
    html_content = result['html']
    
    # 验证脚本标签被过滤
    assert '<script>' not in html_content
    assert 'alert' not in html_content
    # 验证javascript链接被过滤
    assert 'javascript:' not in html_content
    # 验证危险的事件属性被过滤
    assert 'onerror' not in html_content
    
    # 验证合法内容保留
    assert '<h1>' in html_content
    assert '<code>' in html_content
    assert '<pre>' in html_content

def test_comment_xss_protection(app_context, client, test_post):
    """测试评论XSS防护"""
    # 测试包含恶意脚本的评论
    response = client.post(
        f'/post/{test_post.id}/comment',
        data={
            'nickname': 'Test User',
            'email': 'test@example.com',
            'content': '<script>alert("xss")</script><img src="x" onerror="alert(1)">'
        }
    )
    
    # 验证评论创建后的显示
    response = client.get(f'/post/{test_post.id}')
    content = response.data.decode('utf-8')
    assert '<script>' not in content
    assert 'alert' not in content
    assert 'onerror' not in content

def test_csrf_protection(app_context, client):
    """测试CSRF防护"""
    # 测试不带CSRF令牌的POST请求
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 400  # 应该返回400错误
    
    # 获取CSRF令牌
    response = client.get('/admin/login')
    content = response.data.decode('utf-8')
    csrf_token = content.split('csrf_token" value="')[1].split('"')[0]
    
    # 使用正确的CSRF令牌
    response = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302  # 应该重定向到管理页面

def test_password_security(app_context, test_user):
    """测试密码安全性"""
    # 验证密码哈希不可逆
    assert test_user.password_hash != 'password'
    assert test_user.password_hash.startswith('$2b$')  # bcrypt哈希
    
    # 验证原始密码不可访问
    with pytest.raises(AttributeError):
        test_user.password
    
    # 验证密码验证功能
    assert test_user.verify_password('password')
    assert not test_user.verify_password('wrong_password')

def test_session_security(app_context, client, auth):
    """测试会话安全性"""
    # 登录
    auth.login()
    
    # 验证会话cookie
    cookie = next(
        (cookie for cookie in client.cookie_jar if cookie.name == 'session'),
        None
    )
    assert cookie is not None
    assert cookie.secure  # 确保cookie只通过HTTPS发送
    assert cookie.httponly  # 确保cookie不能被JavaScript访问
    
    # 测试会话过期
    client.delete_cookie('session')
    response = client.get('/admin/')
    assert response.status_code == 302  # 应该重定向到登录页面

def test_sql_injection_prevention(app_context, client):
    """测试SQL注入防护"""
    # 测试可能的SQL注入点
    injection_attempts = [
        "' OR '1'='1",
        "; DROP TABLE users;",
        "' UNION SELECT * FROM users;",
        "admin'--",
    ]
    
    for attempt in injection_attempts:
        # 测试登录
        response = client.post('/admin/login', data={
            'username': attempt,
            'password': attempt
        })
        assert response.status_code in [400, 401, 302]  # 应该返回错误或重定向
        
        # 测试搜索
        response = client.get(f'/search?q={attempt}')
        assert response.status_code == 200  # 页面应该正常加载
        assert b'Error' not in response.data  # 不应该暴露数据库错误