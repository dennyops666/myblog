"""
文件名：decorators.py
描述：装饰器函数
作者：denny
创建日期：2024-03-21
"""

from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user

def api_login_required(f):
    """API登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 在测试环境中跳过认证
        if current_app.config.get('TESTING') or current_app.config.get('LOGIN_DISABLED'):
            return f(*args, **kwargs)
            
        if not current_user.is_authenticated:
            return jsonify({'error': '未授权访问'}), 401
        return f(*args, **kwargs)
    return decorated_function 