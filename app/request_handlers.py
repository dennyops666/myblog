from flask import g, session
from app.models.user import User

def register_request_handlers(app):
    """注册请求处理器"""
    
    @app.before_request
    def load_logged_in_user():
        """在请求之前加载已登录的用户"""
        user_id = session.get('user_id')
        
        if user_id is None:
            g.user = None
        else:
            g.user = User.query.get(user_id)
            
    @app.after_request
    def add_security_headers(response):
        """添加安全相关的响应头"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response 