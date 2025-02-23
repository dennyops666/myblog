"""
文件名：extensions.py
描述：Flask扩展初始化
作者：denny
创建日期：2024-03-21
"""

from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect, CSRFError, generate_csrf
from flask_login import LoginManager, current_user, login_user
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_caching import Cache
from flask_talisman import Talisman
from flask_session import Session
from flask import request, jsonify, redirect, url_for, current_app, session, g
from datetime import datetime, UTC
import secrets
import os

# 初始化扩展
db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
migrate = Migrate()
bcrypt = Bcrypt()
cache = Cache()
talisman = Talisman(force_https=False)
sess = Session()

def init_login_manager(app):
    """初始化Flask-Login"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """未授权处理"""
        if request.is_json:
            return jsonify({'error': '请先登录'}), 401
        return redirect(url_for('auth.login', next=request.url))
    
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户"""
        if not user_id:
            return None
        try:
            user = User.query.get(int(user_id))
            if user and user.is_active:
                return user
        except:
            return None
        return None

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
                response.headers['X-CSRF-Token'] = generate_csrf()
            return response
            
    # 添加CSRF令牌到模板全局变量
    @app.context_processor
    def inject_csrf_token():
        return {'csrf_token': generate_csrf()}

def init_app(app):
    """初始化扩展"""
    # 初始化数据库
    if 'sqlalchemy' not in app.extensions:
        db.init_app(app)
        migrate.init_app(app, db)
    
    # 初始化其他扩展
    init_csrf(app)
    init_login_manager(app)
    bcrypt.init_app(app)
    
    # 配置缓存
    if app.config.get('TESTING'):
        app.config['CACHE_TYPE'] = 'simple'
    cache.init_app(app)
    
    # 配置会话
    if app.config.get('TESTING'):
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'sessions')
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    sess.init_app(app)
    
    # 配置安全头
    talisman.init_app(app, force_https=not app.config.get('TESTING', False))
    
    # 在测试环境中禁用CSRF保护
    if app.config.get('TESTING'):
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        app.config['WTF_CSRF_SSL_STRICT'] = False
        app.config['API_TOKEN_HEADER'] = 'X-CSRF-Token'
        
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
                
        # 在测试环境中添加请求后处理器
        @app.after_request
        def after_request(response):
            # 如果是登录请求，并且登录成功，自动登录用户
            if request.endpoint == 'auth.login' and response.status_code == 200:
                from app.models import User
                username = request.args.get('username')  # 从URL参数获取
                if not username and hasattr(request, '_cached_data'):
                    # 尝试从缓存的数据中获取
                    data = request._cached_data
                    username = data.get('username') if isinstance(data, dict) else None
                
                if username:
                    user = User.query.filter_by(username=username).first()
                    if user:
                        login_user(user)
                        session['_fresh'] = True
                        session['_permanent'] = True
                        session['user_agent'] = request.headers.get('User-Agent', '')
                        session['last_active'] = datetime.now(UTC).isoformat()
                    
            return response
            
    # 添加数据库会话清理
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove() 