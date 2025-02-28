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
from flask import request, jsonify, redirect, url_for, current_app, session, g, flash, render_template, make_response
from datetime import datetime, UTC
import secrets
import os
import json
import logging
from logging.handlers import RotatingFileHandler

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
    login_manager.session_protection = None  # 禁用会话保护，避免频繁失效
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'
    login_manager.needs_refresh_message = '会话已过期，请重新登录'
    login_manager.needs_refresh_message_category = 'info'
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """未授权访问处理"""
        if request.is_json:
            return jsonify({
                'success': False,
                'message': '请先登录',
                'csrf_token': generate_csrf()
            }), 401
        return redirect(url_for('auth.login', next=request.url))
    
    @login_manager.user_loader
    def load_user(user_id):
        """加载用户"""
        from app.models import User
        try:
            user = User.query.get(int(user_id))
            if user:
                session.modified = True  # 标记会话已修改，确保会话不会过期
            return user
        except Exception as e:
            current_app.logger.error(f"加载用户失败: {str(e)}")
            return None

def init_csrf(app):
    """初始化CSRF保护"""
    csrf.init_app(app)
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        """处理CSRF错误"""
        if request.is_json:
            return jsonify({
                'success': False,
                'message': '会话已过期，请刷新页面重试',
                'csrf_token': generate_csrf()
            }), 400
        flash('会话已过期，请刷新页面重试', 'danger')
        return redirect(url_for('auth.login'))

    @app.after_request
    def add_csrf_token(response):
        """为每个响应添加CSRF令牌"""
        if response.mimetype == 'text/html':
            response.set_cookie(
                'csrf_token',
                generate_csrf(),
                max_age=3600,  # 1小时
                secure=False,  # 开发环境不要求HTTPS
                httponly=False,  # 允许JavaScript访问
                samesite='Lax'  # 允许跨站请求
            )
        return response

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    migrate.init_app(app, db)

def init_app(app):
    """初始化应用"""
    init_db(app)
    init_login_manager(app)
    init_csrf(app)
    
    @app.after_request
    def add_security_headers(response):
        """添加安全相关的响应头"""
        # 设置内容安全策略
        csp = (
            "default-src 'self' https:; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
            "style-src 'self' 'unsafe-inline' https:; "
            "img-src 'self' data: https:; "
            "font-src 'self' data: https:; "
            "connect-src 'self' https:; "
            "frame-src 'self' https:; "
            "object-src 'none'"
        )
        response.headers['Content-Security-Policy'] = csp
        return response
    
    # 初始化其他扩展
    bcrypt.init_app(app)
    cache.init_app(app)
    talisman.init_app(app)
    sess.init_app(app)
    
    # 注册错误处理器
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误"""
        current_app.logger.warning(f'Bad Request: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e),
            'csrf_token': generate_csrf()
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误"""
        current_app.logger.warning(f'Unauthorized: {str(e)}')
        return jsonify({
            'success': False,
            'message': '未授权访问',
            'csrf_token': generate_csrf()
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误"""
        current_app.logger.warning(f'Forbidden: {str(e)}')
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': False,
                'message': '禁止访问',
                'csrf_token': generate_csrf()
            }), 403
        # 判断是否来自管理后台
        is_admin = request.path.startswith('/admin')
        return render_template('errors/403.html', 
                             message=str(e), 
                             is_admin=is_admin), 403

    @app.errorhandler(404)
    def not_found(e):
        """处理404错误"""
        current_app.logger.warning(f'Not Found: {str(e)}')
        return jsonify({
            'success': False,
            'message': '页面不存在',
            'csrf_token': generate_csrf()
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        current_app.logger.error(f'Server Error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '服务器内部错误',
            'csrf_token': generate_csrf()
        }), 500

    # 添加数据库会话清理
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            current_app.logger.error(f'Exception during request: {str(exception)}')
        db.session.remove() 