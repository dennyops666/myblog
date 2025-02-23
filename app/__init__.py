"""
文件名：__init__.py
描述：应用工厂
作者：denny
创建日期：2024-03-21
"""

import os
from flask import Flask, send_from_directory, g
from flask_wtf.csrf import generate_csrf
from app.config import config
from app.extensions import db, migrate, login_manager, csrf, init_app, cache
from datetime import datetime
from app.controllers.blog import blog_bp
from app.controllers.auth import auth_bp
from app.controllers.admin import admin_bp

def create_app(config_name='development'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    if isinstance(config_name, dict):
        app.config.update(config_name)
    else:
        if config_name not in config:
            config_name = 'default'
        app.config.from_object(config[config_name]())
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
    
    # 配置会话
    if app.config.get('TESTING'):
        app.config['SESSION_TYPE'] = 'filesystem'
        app.config['SESSION_FILE_DIR'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'sessions')
        os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
    
    # 初始化所有扩展
    init_app(app)
    
    # 注册蓝图
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # 注册自定义过滤器
    from app.utils.filters import init_filters
    init_filters(app)
    
    # 添加now过滤器
    @app.template_filter('now')
    def now_filter(format_string):
        """返回当前时间的格式化字符串"""
        return datetime.now().strftime(format_string)
    
    # 添加上传文件访问路由
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)
    
    # 添加CSRF令牌到响应
    @app.after_request
    def add_csrf_token(response):
        if 'text/html' in response.headers.get('Content-Type', ''):
            g.csrf_token = generate_csrf()
        return response
    
    # 添加上下文处理器
    @app.context_processor
    def inject_now():
        return {'now': datetime.now()}
    
    # 初始化配置
    config[config_name if config_name in config else 'default']().init_app(app)
    
    # 在测试环境下初始化数据库
    if app.config.get('TESTING'):
        with app.app_context():
            db.create_all()
            from app.models import Role
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(name='admin', description='Administrator')
                db.session.add(admin_role)
                db.session.commit()
    
    return app
