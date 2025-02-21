"""
文件名：security.py
描述：安全中间件
作者：denny
创建日期：2024-03-21
"""

from functools import wraps
from flask import request, abort, session, current_app
from app.services.security import SecurityService

security_service = SecurityService()

def csrf_protect():
    """CSRF保护装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method not in ['GET', 'HEAD', 'OPTIONS']:
                # 在测试环境中跳过CSRF验证
                if current_app.config.get('TESTING'):
                    return f(*args, **kwargs)
                    
                # 从请求中获取CSRF令牌
                csrf_token = request.headers.get('X-CSRF-Token')
                if not csrf_token:
                    csrf_token = request.form.get('csrf_token')
                
                # 验证CSRF令牌
                if not csrf_token or not security_service.validate_csrf_token(csrf_token):
                    abort(400, description='CSRF token is missing or invalid')
                
                # 生成新的CSRF令牌
                new_csrf_token = security_service.generate_csrf_token()
                session['csrf_token'] = new_csrf_token
                session['_fresh'] = True
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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

def rate_limit(limit=100, per=60):
    """速率限制装饰器
    
    Args:
        limit: 允许的最大请求次数
        per: 时间窗口（秒）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 获取客户端IP
            ip = request.remote_addr
            
            # 检查是否超过限制
            key = f'rate_limit:{ip}'
            current = current_app.cache.get(key) or 0
            
            if current >= limit:
                abort(429, description='Too many requests')
            
            # 更新计数器
            current_app.cache.set(key, current + 1, timeout=per)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 