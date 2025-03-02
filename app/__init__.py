"""
文件名：__init__.py
描述：Flask应用初始化
作者：denny
创建日期：2024-03-21
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_from_directory, g, render_template, request, jsonify, redirect, url_for
from flask_migrate import Migrate
from app.config import config
from app.extensions import db, init_app, migrate
from datetime import datetime, UTC, timedelta
from app.controllers.blog import blog
from app.controllers.auth import auth_bp
from app.controllers.admin import admin_bp
from app.controllers.admin.upload import upload_bp
from app.controllers.test import test_bp
import traceback
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from app.utils.markdown import markdown_to_html
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect

# 创建 migrate 实例
migrate = Migrate()

# 配置登录管理器
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

# 配置自定义过滤器
csrf = CSRFProtect()

moment = Moment()

def create_app(config_name='development'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置会话
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # 允许非HTTPS
        SESSION_COOKIE_HTTPONLY=True,  # 防止JavaScript访问
        SESSION_COOKIE_SAMESITE='Lax',  # 允许跨站点请求
        PERMANENT_SESSION_LIFETIME=timedelta(days=365),  # 延长会话有效期
        SESSION_REFRESH_EACH_REQUEST=True,  # 每次请求都刷新会话
    )
    
    # 确保日志目录存在
    log_dir = '/data/myblog/logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志处理器
    log_file = os.path.join(log_dir, 'myblog.log')
    error_log_file = os.path.join(log_dir, 'error.log')
    
    # 设置日志文件权限
    for log_path in [log_file, error_log_file]:
        if os.path.exists(log_path):
            os.chmod(log_path, 0o666)
            
    # 主日志处理器
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s\n%(exc_info)s'
    ))
    file_handler.setLevel(logging.INFO)
    
    # 错误日志处理器
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s\n%(exc_info)s'
    ))
    error_handler.setLevel(logging.ERROR)
    
    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s\n%(exc_info)s'
    ))
    console_handler.setLevel(logging.DEBUG if app.debug else logging.INFO)
    
    # 设置日志级别和处理器
    app.logger.setLevel(logging.DEBUG if app.debug else logging.INFO)
    app.logger.handlers = []  # 清除默认处理器
    app.logger.addHandler(file_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    
    # 记录启动信息
    app.logger.info('MyBlog 启动')
    app.logger.info('配置模式: %s', config_name)
    app.logger.info('调试模式: %s', app.debug)
    app.logger.info('日志目录: %s', log_dir)
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
    
    # 配置会话
    if app.config.get('TESTING'):
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        app.config['SESSION_SQLALCHEMY'] = db
    
    # 注册markdown过滤器
    app.jinja_env.filters['markdown'] = markdown_to_html
    
    # 初始化所有扩展
    try:
        init_app(app)
        app.logger.info('扩展初始化完成')
        
        # 添加favicon路由
        @app.route('/favicon.ico')
        def favicon():
            return send_from_directory(
                os.path.join(app.root_path, 'static'),
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )
            
        # 添加根路由重定向
        @app.route('/')
        def index():
            return redirect(url_for('blog.index'))
        
        # 注册蓝图
        app.register_blueprint(blog, url_prefix='/blog')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(test_bp, url_prefix='/test')
        app.logger.info('蓝图注册完成')
        
        # 初始化 Flask-Migrate
        migrate.init_app(app, db)
        app.logger.info('数据库迁移初始化完成')
        
        # 初始化测试数据
        if app.config['TESTING']:
            from tests.test_data import init_test_data
            init_test_data(app)
            app.logger.info('测试数据库初始化完成')
        
        # 初始化其他扩展
        moment.init_app(app)
        login_manager.init_app(app)
        csrf.init_app(app)
        
        app.logger.info('应用初始化完成')
        return app
        
    except Exception as e:
        app.logger.error('应用初始化失败: %s', str(e))
        app.logger.error('错误详情: %s', traceback.format_exc())
        raise
