"""
文件名：security.py
描述：安全中间件
作者：denny
创建日期：2024-03-21
"""

from functools import wraps
from flask import request, redirect, url_for, jsonify, current_app
from flask_login import current_user
import time
from app.models.permission import Permission

def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '请先登录'
                })
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '请先登录'
                })
            return redirect(url_for('auth.login'))
        
        if not current_user.has_permission(Permission.ADMIN):
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '需要管理员权限'
                })
            return redirect(url_for('blog.index'))
            
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    """权限验证装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '请先登录'
                    })
                return redirect(url_for('auth.login'))
                
            if not current_user.has_permission(permission):
                if request.is_xhr:
                    return jsonify({
                        'success': False,
                        'message': '权限不足'
                    })
                return redirect(url_for('blog.index'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class RateLimiter:
    """请求频率限制器"""
    def __init__(self, max_requests=60, time_window=60):
        self.max_requests = max_requests  # 最大请求次数
        self.time_window = time_window    # 时间窗口（秒）
        self.requests = {}                # 请求记录
        
    def is_allowed(self, key):
        """检查请求是否允许"""
        current_time = time.time()
        
        # 清理过期的请求记录
        self._cleanup(current_time)
        
        # 获取当前key的请求记录
        if key not in self.requests:
            self.requests[key] = []
            
        request_times = self.requests[key]
        
        # 检查是否超过限制
        if len(request_times) >= self.max_requests:
            return False
            
        # 记录新的请求
        request_times.append(current_time)
        return True
        
    def _cleanup(self, current_time):
        """清理过期的请求记录"""
        cutoff_time = current_time - self.time_window
        
        for key in list(self.requests.keys()):
            self.requests[key] = [t for t in self.requests[key] if t > cutoff_time]
            if not self.requests[key]:
                del self.requests[key]

# 创建全局限速器实例
rate_limiter = RateLimiter()

def rate_limit(f):
    """请求频率限制装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取客户端标识（IP地址）
        client_ip = request.remote_addr
        
        # 检查是否允许请求
        if not rate_limiter.is_allowed(client_ip):
            if request.is_xhr:
                return jsonify({
                    'success': False,
                    'message': '请求过于频繁，请稍后再试'
                })
            return redirect(url_for('blog.index'))
            
        return f(*args, **kwargs)
    return decorated_function

def xss_protect():
    """XSS保护装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                # 清理表单数据
                if request.form:
                    for key, value in request.form.items():
                        if isinstance(value, str):
                            request.form = request.form.copy()
                            request.form[key] = security_service.sanitize_input(value)
                
                # 清理JSON数据
                if request.is_json:
                    data = request.get_json()
                    if data:
                        request._cached_json = (security_service.sanitize_input(data), request._cached_json[1])
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sql_injection_protect():
    """SQL注入保护装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                # 检查表单数据
                if request.form:
                    for value in request.form.values():
                        if isinstance(value, str) and check_sql_injection(value):
                            abort(400, description='Potential SQL injection detected')
                
                # 检查JSON数据
                if request.is_json:
                    data = request.get_json()
                    if data:
                        if isinstance(data, dict):
                            for value in data.values():
                                if isinstance(value, str) and check_sql_injection(value):
                                    abort(400, description='Potential SQL injection detected')
                        elif isinstance(data, str) and check_sql_injection(data):
                            abort(400, description='Potential SQL injection detected')
            
            return f(*args, **kwargs)
        
        def check_sql_injection(value):
            """检查SQL注入"""
            # SQL注入关键字
            sql_keywords = [
                'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION',
                'WHERE', 'OR', 'AND', '--', ';', '1=1', 'LIKE', 'IN'
            ]
            
            # 特殊字符
            special_chars = ["'", '"', '\\', ';', '--', '/*', '*/']
            
            value = value.upper()
            # 检查SQL关键字
            for keyword in sql_keywords:
                if f' {keyword} ' in f' {value} ':
                    return True
            
            # 检查特殊字符
            for char in special_chars:
                if char in value:
                    return True
            
            return False
            
        return decorated_function
    return decorator

def secure_headers():
    """安全响应头装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # 添加安全响应头
            headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1; mode=block',
                'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
                'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
                'Referrer-Policy': 'strict-origin-when-cross-origin',
                'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
                'Pragma': 'no-cache'
            }
            
            # 将安全响应头添加到响应中
            for header, value in headers.items():
                response.headers[header] = value
            
            return response
        return decorated_function
    return decorator

def validate_csrf():
    """验证 CSRF Token"""
    # 禁用 CSRF 验证
    return True 