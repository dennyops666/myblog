"""
文件名：__init__.py
描述：Flask应用初始化
作者：denny
创建日期：2024-03-21
"""

import os
from flask import Flask, request, jsonify, session, g
from flask_login import current_user
from app.extensions import db, migrate, login_manager, csrf, cache
from app.models.user import User
from app.services.security import SecurityService
import secrets
from datetime import datetime, UTC
from flask import send_from_directory
from flask_wtf.csrf import generate_csrf

def create_app(config=None):
    """创建 Flask 应用实例"""
    app = Flask(__name__)
    
    # 加载默认配置
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///blog.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.instance_path, 'uploads'),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_CHECK_DEFAULT=True,
        WTF_CSRF_TIME_LIMIT=3600,
        LOGIN_VIEW='auth.login',
        LOGIN_MESSAGE='请先登录',
        SESSION_PROTECTION='strong'
    )
    
    # 如果提供了配置，则更新
    if config is not None:
        app.config.update(config)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # 注册蓝图
    from .controllers.admin import admin_bp
    from .controllers.auth import auth_bp
    
    app.register_blueprint(auth_bp, url_prefix='/admin')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 添加上传文件路由
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    
    # 添加 CSRF 令牌到响应头
    @app.after_request
    def add_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            response.headers['X-CSRF-Token'] = generate_csrf()
        return response
    
    return app
