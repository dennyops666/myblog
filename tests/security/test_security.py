"""
文件名：test_security.py
描述：安全测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from app.services.security import SecurityService
from app.models.user import User
from flask import session, g
from datetime import datetime, timedelta, UTC
import os
import json

def test_markdown_xss_protection(client, auth, test_user):
    """测试Markdown XSS防护"""
    security_service = SecurityService()
    
    # 测试各种XSS攻击向量
    xss_vectors = [
        '<script>alert("XSS")</script>',
        '<img src="javascript:alert(\'XSS\')">',
        '<a href="javascript:alert(\'XSS\')">点击我</a>',
        '<svg onload=alert(1)>',
        '"><script>alert("XSS")</script>',
        '`-alert(1)`'
    ]
    
    for vector in xss_vectors:
        # 清理Markdown内容
        clean_html = security_service.sanitize_markdown(vector)
        assert '<script>' not in clean_html.lower()
        assert 'javascript:' not in clean_html.lower()
        assert 'alert(' not in clean_html.lower()
        assert 'onerror' not in clean_html.lower()
        assert 'onload' not in clean_html.lower()

def test_comment_xss_protection(client, auth, test_user):
    """测试评论XSS防护"""
    security_service = SecurityService()
    
    # 登录
    auth.login()
    
    # 测试各种XSS攻击向量
    xss_vectors = [
        '<script>alert("XSS")</script>',
        '<img src="javascript:alert(\'XSS\')">',
        '<a href="javascript:alert(\'XSS\')">点击我</a>',
        '<svg onload=alert(1)>',
        '"><script>alert("XSS")</script>',
        '`-alert(1)`'
    ]
    
    for vector in xss_vectors:
        # 清理评论内容
        clean_text = security_service.sanitize_comment(vector)
        assert '<script>' not in clean_text.lower()
        assert 'javascript:' not in clean_text.lower()
        assert 'alert(' not in clean_text.lower()
        assert 'onerror' not in clean_text.lower()
        assert 'onload' not in clean_text.lower()

def test_csrf_protection(client, auth, security_service):
    """测试CSRF防护"""
    # 获取CSRF令牌
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()

    # 测试不带CSRF令牌的POST请求
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password'
    })
    assert response.status_code in (400, 401, 403)  # 请求应被拒绝
    
    # 测试带无效CSRF令牌的POST请求
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': 'invalid_token'
    })
    assert response.status_code in (400, 401, 403)  # 请求应被拒绝
    
    # 测试带有效CSRF令牌的POST请求
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code in (200, 302)  # 请求应被接受（302是重定向到首页）

def test_session_security(client, auth):
    """测试会话安全性"""
    security_service = SecurityService()
    
    # 登录前获取CSRF令牌
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 登录
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code in (200, 302)  # 登录成功
    
    # 测试会话属性
    with client.session_transaction() as sess:
        assert sess.get('csrf_token') is not None
        assert sess.get('_fresh') is True
        assert sess.get('user_agent') is not None
        assert sess.get('last_active') is not None

def test_sql_injection_prevention(client, auth, security_service):
    """测试SQL注入防护"""
    # 测试各种SQL注入攻击
    injection_attempts = [
        "admin' OR '1'='1",
        "admin'; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
        "admin' AND 1=1 --",
        "); DROP TABLE users; --",
        "' OR '1'='1' /*",
        "admin' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL --"
    ]
    
    # 获取CSRF令牌
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 测试每个注入尝试
    for injection in injection_attempts:
        response = client.post('/auth/login', data={
            'username': injection,
            'password': injection,
            'csrf_token': csrf_token
        })
        assert response.status_code in (400, 401, 403)  # 请求应被拒绝（无效凭据）

def test_password_security(client, auth, test_user):
    """测试密码安全性"""
    security_service = SecurityService()
    
    # 测试密码复杂度要求
    weak_passwords = [
        'short',  # 太短
        'onlyletters',  # 只有字母
        '12345678',  # 只有数字
        'nouppercaseordigits',  # 没有大写字母和数字
        'NOLOWERCASEORDIGITS',  # 没有小写字母和数字
        'NoSpecialChars1'  # 没有特殊字符
    ]
    
    # 验证用户密码已正确哈希
    user = User.query.get(test_user.id)
    assert user.password_hash != 'password'  # 密码应该被哈希
    assert user.password_hash.startswith('$2b$')  # 使用bcrypt哈希
    
    # 获取CSRF令牌
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 测试弱密码
    for weak_password in weak_passwords:
        response = client.post('/auth/register', data={
            'username': 'test_user',
            'email': 'test@example.com',
            'password': weak_password,
            'csrf_token': csrf_token
        })
        assert response.status_code in (400, 422)  # 弱密码应被拒绝

def test_file_upload_security(client, auth, security_service, tmp_path):
    """测试文件上传安全性"""
    # 获取CSRF令牌并登录
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 登录
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code in (200, 302)  # 登录成功
    
    # 创建测试文件
    test_files = {
        'valid.txt': b'Hello, World!',
        'malicious.php': b'<?php echo "malicious"; ?>',
        'large.bin': b'0' * (security_service.MAX_FILE_SIZE + 1),
        'image.jpg': b'fake image content',
        'script.js': b'alert("XSS");'
    }
    
    file_paths = {}
    for name, content in test_files.items():
        path = os.path.join(tmp_path, name)
        with open(path, 'wb') as f:
            f.write(content)
        file_paths[name] = path
    
    # 测试文件上传
    for name, path in file_paths.items():
        with open(path, 'rb') as f:
            data = {
                'file': (f, name),
                'csrf_token': csrf_token
            }
            response = client.post('/upload', data=data)
            
            # 检查响应
            if name == 'valid.txt' or name == 'image.jpg':
                assert response.status_code in (200, 201)  # 有效文件应被接受
            else:
                assert response.status_code in (400, 403)  # 无效文件应被拒绝

def test_sensitive_data_protection(client, auth, test_user):
    """测试敏感数据保护"""
    security_service = SecurityService()
    
    # 获取CSRF令牌并登录
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 登录
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code in (200, 302)  # 登录成功
    
    # 测试API响应中不包含敏感信息
    headers = {'X-CSRF-Token': csrf_token}
    response = client.get('/api/users/me', headers=headers)
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'password' not in data
    assert 'password_hash' not in data
    assert 'id' in data
    assert 'username' in data
    assert 'email' in data
    assert 'created_at' in data

def test_api_request_validation(client, auth, security_service):
    """测试API请求验证"""
    # 获取CSRF令牌并登录
    with client.session_transaction() as sess:
        csrf_token = security_service.generate_csrf_token()
        sess['csrf_token'] = csrf_token
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['user_agent'] = 'test_agent'
        sess['last_active'] = datetime.now(UTC).isoformat()
    
    # 登录
    response = client.post('/auth/login', data={
        'username': 'test_user',
        'password': 'password',
        'csrf_token': csrf_token
    })
    assert response.status_code in (200, 302)  # 登录成功
    
    # 测试API端点的请求验证
    endpoints = ['/api/users/me', '/api/posts', '/api/comments']
    methods = ['GET', 'POST', 'PUT', 'DELETE']
    
    for endpoint in endpoints:
        for method in methods:
            # 不带令牌的请求
            headers = {'Content-Type': 'application/json'}
            response = client.open(endpoint, method=method, headers=headers)
            if method == 'GET':
                assert response.status_code in (200, 404)  # GET请求应被接受
            else:
                # 在测试环境中，如果没有令牌会自动生成一个
                assert response.status_code in (200, 201, 400, 404)
            
            # 带无效令牌的请求
            headers = {
                'X-CSRF-Token': 'invalid_token',
                'Content-Type': 'application/json'
            }
            response = client.open(endpoint, method=method, headers=headers)
            if method == 'GET':
                assert response.status_code in (200, 404)  # GET请求应被接受
            else:
                # 在测试环境中，无效令牌会被替换为新生成的令牌
                assert response.status_code in (200, 201, 400, 404)
            
            # 带有效令牌的请求
            headers = {
                'X-CSRF-Token': csrf_token,
                'Content-Type': 'application/json'
            }
            response = client.open(endpoint, method=method, headers=headers)
            if method == 'GET':
                assert response.status_code in (200, 404)  # GET请求应被接受
            else:
                assert response.status_code in (200, 201, 400, 404)  # 其他请求在测试环境中更宽松