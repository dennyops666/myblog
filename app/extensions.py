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
import json

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
    login_manager.login_message_category = 'warning'
    
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
            from app.models import User
            user = db.session.get(User, int(user_id))
            if user and user.is_active:
                return user
        except:
            return None
        return None

def init_csrf(app):
    """初始化 CSRF 保护"""
    # 在测试环境中不启用 CSRF 保护
    if app.config.get('TESTING'):
        app.config['WTF_CSRF_ENABLED'] = False
    csrf.init_app(app)

    def handle_csrf_error(e):
        """处理 CSRF 错误"""
        if request.is_json:
            return jsonify({
                'code': 400,
                'message': '无效的 CSRF 令牌'
            }), 400
        return redirect(url_for('auth.login'))

    app.register_error_handler(CSRFError, handle_csrf_error)

    @app.after_request
    def add_csrf_token(response):
        """为响应添加 CSRF 令牌"""
        if not app.config.get('TESTING'):
            token = generate_csrf()
            response.headers.set('X-CSRF-Token', token)
        return response

    @app.context_processor
    def inject_csrf_token():
        """注入 CSRF 令牌到模板"""
        if not app.config.get('TESTING'):
            return dict(csrf_token=generate_csrf())
        return dict(csrf_token='')

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
        app.config['CACHE_TYPE'] = 'SimpleCache'
    cache.init_app(app)
    
    # 配置会话
    if not app.config.get('SESSION_SQLALCHEMY'):
        app.config['SESSION_SQLALCHEMY'] = db
    sess.init_app(app)
    
    # 配置安全头
    talisman.init_app(app, force_https=not app.config.get('TESTING', False))
    
    # 在测试环境中配置CSRF保护
    if app.config.get('TESTING'):
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['WTF_CSRF_CHECK_DEFAULT'] = False
        app.config['WTF_CSRF_SSL_STRICT'] = False
        
        # 在测试环境中添加请求前处理器
        @app.before_request
        def handle_test_request():
            # 跳过OPTIONS请求
            if request.method == 'OPTIONS':
                return None
                
            # 如果是已登录用户的请求，确保会话数据正确
            if current_user.is_authenticated:
                session['_fresh'] = True
                session['_permanent'] = True
                session['_user_id'] = str(current_user.id)
                session['_id'] = current_user.get_id()
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
        if hasattr(g, 'session'):
            g.session.close()

    # 注册错误处理器
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误"""
        return jsonify({
            'success': False,
            'message': str(e),
            'csrf_token': generate_csrf()
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误"""
        return jsonify({
            'success': False,
            'message': '未授权访问',
            'csrf_token': generate_csrf()
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误"""
        return jsonify({
            'success': False,
            'message': '禁止访问',
            'csrf_token': generate_csrf()
        }), 403

    @app.errorhandler(404)
    def not_found(e):
        """处理404错误"""
        return jsonify({
            'success': False,
            'message': '资源不存在',
            'csrf_token': generate_csrf()
        }), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        """处理413错误"""
        return jsonify({
            'success': False,
            'message': '文件太大',
            'csrf_token': generate_csrf()
        }), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'csrf_token': generate_csrf()
        }), 500

    # 配置CSRF错误处理
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """处理CSRF错误"""
        token = generate_csrf()
        response = jsonify({
            'success': False,
            'message': f'CSRF验证失败: {str(e)}',
            'csrf_token': token
        })
        response.status_code = 400
        return response

    # 为每个响应添加CSRF token
    @app.after_request
    def add_csrf_token(response):
        """为每个响应添加CSRF token"""
        if request.endpoint != 'static':
            token = generate_csrf()
            response.set_cookie('csrf_token', token)
            if response.is_json:
                data = response.get_json()
                if isinstance(data, dict):
                    data['csrf_token'] = token
                    response.data = current_app.json.dumps(data)
        return response 