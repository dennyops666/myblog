"""
文件名：security.py
描述：安全相关的工具函数
作者：denny
"""

import os
import jwt
from datetime import datetime, timedelta, UTC
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash

def generate_token(data, expiration=3600):
    """生成JWT令牌
    
    Args:
        data: 要编码的数据，可以是用户ID或包含用户ID和操作的字典
        expiration: 过期时间（秒）
        
    Returns:
        str: JWT令牌
    """
    now = datetime.now(UTC)
    payload = {
        'exp': now + timedelta(seconds=expiration),
        'iat': now,
        'jti': os.urandom(16).hex()
    }
    
    # 如果data是字典，则合并到payload中
    if isinstance(data, dict):
        payload.update(data)
    else:
        # 向后兼容，如果data是用户ID，则添加user_id字段
        payload['user_id'] = data
        
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_token(token):
    """验证JWT令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        dict|None: 解码后的数据，如果令牌无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
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