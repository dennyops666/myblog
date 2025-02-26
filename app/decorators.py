"""
文件名：decorators.py
描述：装饰器函数
作者：denny
创建日期：2024-03-21
"""

from functools import wraps
from flask import jsonify, request, current_app, abort, flash, redirect, url_for
from flask_login import current_user
from app.models.permission import Permission
from flask_wtf.csrf import generate_csrf

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

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 在测试环境中跳过认证
        if current_app.config.get('TESTING') or current_app.config.get('LOGIN_DISABLED'):
            return f(*args, **kwargs)
            
        # 检查是否是API请求
        is_api_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or \
                        request.headers.get('Accept') == 'application/json'
            
        if not current_user.is_authenticated:
            if is_api_request:
                return jsonify({
                    'success': False,
                    'message': '请先登录后再访问',
                    'csrf_token': generate_csrf()
                }), 401
            return abort(401, description='请先登录后再访问')
        
        # 检查用户是否具有管理员权限
        if not current_user.roles:
            if is_api_request:
                return jsonify({
                    'success': False,
                    'message': '您没有管理员权限，无法访问此页面',
                    'csrf_token': generate_csrf()
                }), 403
            return abort(403, description='您没有管理员权限，无法访问此页面')
            
        has_admin = False
        for role in current_user.roles:
            if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                has_admin = True
                break
                
        if not has_admin:
            if is_api_request:
                return jsonify({
                    'success': False,
                    'message': '您没有管理员权限，无法访问此页面',
                    'csrf_token': generate_csrf()
                }), 403
            return abort(403, description='您没有管理员权限，无法访问此页面')
            
        return f(*args, **kwargs)
    return decorated_function 