"""
文件名：security.py
描述：安全工具模块
作者：denny
创建日期：2024-03-21
"""

import os
import jwt
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def generate_token(user_id, expires_in=3600):
    """生成JWT令牌"""
    now = datetime.utcnow()
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