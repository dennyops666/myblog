"""
文件名：security.py
描述：安全相关的工具函数和装饰器
作者：denny
创建日期：2024-03-21
"""

import os
import jwt
from datetime import datetime, timedelta, UTC
from flask import current_app, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re

def generate_token(user_id, expires_in=3600):
    """生成JWT令牌"""
    now = datetime.now(UTC)
    payload = {
        'user_id': user_id,
        'exp': now + timedelta(seconds=expires_in),
        'iat': now,
        'jti': os.urandom(16).hex()
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_token(token):
    """验证JWT令牌"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload.get('user_id')
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def hash_password(password):
    """哈希密码"""
    return generate_password_hash(password)

def check_password(password_hash, password):
    """验证密码"""
    return check_password_hash(password_hash, password)

def generate_random_string(length=32):
    """生成随机字符串"""
    return os.urandom(length).hex()

def is_safe_url(url):
    """检查URL是否安全"""
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, url))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc

def sanitize_redirect_url(url, default='/'):
    """清理重定向URL"""
    return url if url and is_safe_url(url) else default

def sql_injection_protect():
    """SQL注入防护装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取请求参数
            params = {}
            if request.method == 'GET':
                params.update(request.args.to_dict())
            elif request.method == 'POST':
                if request.is_json:
                    params.update(request.get_json())
                else:
                    params.update(request.form.to_dict())
            
            # SQL注入检测模式
            sql_patterns = [
                r'(\s|^)(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)(\s|$)',
                r'(\s|^)(OR|AND)(\s+)(\d+|\'[^\']*\'|\"[^\"]*\")(\s*)(=|>|<|>=|<=)(\s*)(\d+|\'[^\']*\'|\"[^\"]*\")',
                r'--',
                r';',
                r'\/\*.*\*\/',
                r'#',
                r'EXEC(\s|\().*(\)|$)',
                r'xp_.*',
            ]
            
            # 检查所有参数
            for value in params.values():
                if isinstance(value, str):
                    for pattern in sql_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            return jsonify({'error': '检测到潜在的SQL注入攻击'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def xss_protect():
    """XSS防护装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取请求参数
            params = {}
            if request.method == 'GET':
                params.update(request.args.to_dict())
            elif request.method == 'POST':
                if request.is_json:
                    params.update(request.get_json())
                else:
                    params.update(request.form.to_dict())
            
            # XSS检测模式
            xss_patterns = [
                r'<script.*?>.*?<\/script>',
                r'javascript:',
                r'vbscript:',
                r'onload=',
                r'onerror=',
                r'onclick=',
                r'onmouseover=',
                r'onfocus=',
                r'onblur=',
                r'alert\s*\(',
                r'eval\s*\(',
                r'document\.cookie',
                r'document\.write',
                r'document\.location',
                r'<iframe.*?>',
                r'<object.*?>',
                r'<embed.*?>',
            ]
            
            # 检查所有参数
            for value in params.values():
                if isinstance(value, str):
                    for pattern in xss_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            return jsonify({'error': '检测到潜在的XSS攻击'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 