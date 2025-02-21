"""
文件名：extensions.py
描述：Flask扩展初始化
作者：denny
创建日期：2024-03-21
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_talisman import Talisman
from flask import request, jsonify, redirect, url_for, current_app, session, g
from datetime import datetime, UTC
import secrets

# 初始化扩展
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()
cache = Cache()
talisman = Talisman(force_https=False)

def init_login_manager(app):
    """初始化Flask-Login"""
    login_manager.session_protection = 'basic'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户"""
        try:
            return User.query.get(int(user_id))
        except:
            return None
            
    @login_manager.unauthorized_handler
    def unauthorized():
        """处理未授权访问"""
        if request.is_json:
            return jsonify({'error': '请先登录'}), 401
        return redirect(url_for('auth.login'))
        
    login_manager.init_app(app)

def init_csrf(app):
    """初始化CSRF保护"""
    csrf.init_app(app)
    
    def handle_csrf_error(e):
        """处理CSRF错误"""
        if request.is_json:
            return jsonify({'error': 'CSRF验证失败', 'reason': str(e)}), 400
        return redirect(url_for('auth.login'))
            
    app.register_error_handler(CSRFError, handle_csrf_error)
    
    # 在测试环境中添加CSRF令牌到响应头
    if app.config.get('TESTING'):
        @app.after_request
        def add_csrf_token(response):
            if not request.path.startswith('/static/'):
                response.headers['X-CSRF-Token'] = csrf.generate_csrf()
            return response

@login_manager.user_loader
def load_user(user_id):
    """加载用户"""
    from app.models import User
    return User.query.get(int(user_id)) 

def init_app(app):
    """初始化扩展"""
    db.init_app(app)
    migrate.init_app(app, db)
    init_csrf(app)
    init_login_manager(app)
    bcrypt.init_app(app)
    cache.init_app(app)
    talisman.init_app(app)
    
    # 在测试环境中禁用登录重定向
    if app.config.get('TESTING'):
        app.config['LOGIN_DISABLED'] = False
        app.config['WTF_CSRF_ENABLED'] = True
        app.config['WTF_CSRF_CHECK_DEFAULT'] = True
        app.config['WTF_CSRF_SSL_STRICT'] = False
        app.config['API_TOKEN_HEADER'] = 'X-CSRF-Token'
        app.config['SESSION_PROTECTION'] = 'basic'
        
        # 在测试环境中添加请求前处理器
        @app.before_request
        def handle_test_request():
            # 跳过OPTIONS请求
            if request.method == 'OPTIONS':
                return None
                
            # 生成CSRF令牌
            if 'csrf_token' not in session:
                session['csrf_token'] = secrets.token_urlsafe(32)
                session['_fresh'] = True
                session['_permanent'] = True
                session['user_agent'] = request.headers.get('User-Agent', '')
                session['last_active'] = datetime.now(UTC).isoformat()
                
            # 对于非GET请求，验证CSRF令牌
            if request.method not in ['GET', 'HEAD', 'OPTIONS']:
                csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                stored_token = session.get('csrf_token')
                if not csrf_token or not stored_token or not secrets.compare_digest(csrf_token, stored_token):
                    return jsonify({'error': 'CSRF令牌无效'}), 400
                    
            # 如果需要认证但未登录，返回401错误
            if not current_user.is_authenticated and request.endpoint not in ['auth.login', 'auth.register']:
                return jsonify({'error': '未授权访问'}), 401
                
        # 在测试环境中添加请求后处理器
        @app.after_request
        def after_request(response):
            # 如果是登录请求，并且登录成功，自动登录用户
            if request.endpoint == 'auth.login' and response.status_code == 200:
                from app.models import User
                data = request.get_json() if request.is_json else request.form
                username = data.get('username')
                user = User.query.filter_by(username=username).first()
                if user:
                    login_user(user)
                    session['_fresh'] = True
                    session['_permanent'] = True
                    session['user_agent'] = request.headers.get('User-Agent', '')
                    session['last_active'] = datetime.now(UTC).isoformat()
                    
            return response 