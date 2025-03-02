"""
文件名：extensions.py
描述：Flask扩展初始化
作者：denny
创建日期：2024-03-21
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_caching import Cache
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask import request, jsonify, redirect, url_for, current_app, session, g, flash, render_template, make_response
from datetime import datetime, UTC
import secrets
import os
import json
import logging
from logging.handlers import RotatingFileHandler

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cache = Cache()
bcrypt = Bcrypt()
sess = Session()

def init_app(app):
    """初始化所有扩展"""
    # 首先初始化SQLAlchemy
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 配置Session使用已存在的SQLAlchemy实例
    app.config['SESSION_SQLALCHEMY'] = db
    
    # 初始化其他扩展
    login_manager.init_app(app)
    cache.init_app(app)
    bcrypt.init_app(app)
    sess.init_app(app)
    
    # 配置登录管理器
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'
    
    # 添加空的csrf_token函数
    @app.context_processor
    def inject_csrf_token():
        def csrf_token():
            return ""
        return dict(csrf_token=csrf_token)
    
    # 注册用户加载函数
    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.after_request
    def add_security_headers(response):
        """添加安全相关的响应头"""
        # 移除现有的CSP头
        response.headers.pop('Content-Security-Policy', None)
        response.headers.pop('X-Content-Security-Policy', None)
        
        # 设置其他安全头
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response
    
    # 注册错误处理器
    @app.errorhandler(400)
    def bad_request(e):
        """处理400错误"""
        current_app.logger.warning(f'Bad Request: {str(e)}')
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

    @app.errorhandler(401)
    def unauthorized(e):
        """处理401错误"""
        current_app.logger.warning(f'Unauthorized: {str(e)}')
        return jsonify({
            'success': False,
            'message': '未授权访问'
        }), 401

    @app.errorhandler(403)
    def forbidden(e):
        """处理403错误"""
        current_app.logger.warning(f'Forbidden: {str(e)}')
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': False,
                'message': '禁止访问'
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
            'message': '页面不存在'
        }), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        """处理500错误"""
        current_app.logger.error(f'Server Error: {str(e)}')
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '服务器内部错误'
        }), 500

    # 添加数据库会话清理
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        if exception:
            current_app.logger.error(f'Exception during request: {str(exception)}')
        db.session.remove() 