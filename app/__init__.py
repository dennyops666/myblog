"""
文件名：__init__.py
描述：应用工厂
作者：denny
创建日期：2024-03-21
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_from_directory, g, render_template, request, jsonify
from flask_wtf.csrf import generate_csrf
from flask_migrate import Migrate
from app.config import config
from app.extensions import db, init_app
from datetime import datetime, UTC, timedelta
from app.controllers.blog import blog_bp
from app.controllers.auth import auth_bp
from app.controllers.admin import admin_bp
from app.controllers.admin.upload import upload_bp

# 创建 migrate 实例
migrate = Migrate()

def create_app(config_name='development'):
    """创建Flask应用实例"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置会话
    app.config.update(
        WTF_CSRF_ENABLED=False,  # 禁用CSRF保护
        WTF_CSRF_CHECK_DEFAULT=False,  # 禁用默认的CSRF检查
        SESSION_COOKIE_SECURE=False,  # 允许非HTTPS
        SESSION_COOKIE_HTTPONLY=True,  # 防止JavaScript访问
        SESSION_COOKIE_SAMESITE='Lax',  # 允许跨站点请求
        PERMANENT_SESSION_LIFETIME=timedelta(days=365),  # 延长会话有效期
        SESSION_REFRESH_EACH_REQUEST=True,  # 每次请求都刷新会话
    )
    
    # 获取应用根目录
    app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 确保日志目录存在
    log_dir = os.path.join(app_root, 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 配置日志处理器
    log_file = os.path.join(log_dir, 'myblog.log')
    if os.path.exists(log_file):
        os.chmod(log_file, 0o666)
    file_handler = RotatingFileHandler(log_file, maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    # 配置控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    console_handler.setLevel(logging.DEBUG)
    app.logger.addHandler(console_handler)
    
    # 设置日志级别
    app.logger.setLevel(logging.DEBUG)
    
    # 移除默认的处理器
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    
    # 记录启动信息
    app.logger.info('MyBlog 启动')
    app.logger.info(f'配置模式: {config_name}')
    app.logger.info(f'调试模式: {app.debug}')
    app.logger.info(f'日志文件: {log_file}')
    
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)
    
    # 配置会话
    if app.config.get('TESTING'):
        app.config['SESSION_TYPE'] = 'sqlalchemy'
        app.config['SESSION_SQLALCHEMY'] = db
    
    # 初始化所有扩展
    init_app(app)
    app.logger.info('扩展初始化完成')
    
    # 初始化 Flask-Migrate
    migrate.init_app(app, db)
    app.logger.info('数据库迁移初始化完成')
    
    # 注册蓝图
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(upload_bp, url_prefix='/admin/upload')
    app.logger.info('蓝图注册完成')
    
    # 注册错误处理器
    @app.errorhandler(500)
    def internal_error(error):
        """处理500错误"""
        app.logger.error(f'服务器错误: {str(error)}')
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(404)
    def not_found_error(error):
        """处理404错误"""
        app.logger.warning(f'页面未找到: {request.url}')
        return render_template('errors/404.html'), 404
    
    # 注册自定义过滤器
    from app.utils.filters import init_filters
    init_filters(app)
    app.logger.info('过滤器初始化完成')
    
    # 添加now过滤器
    @app.template_filter('now')
    def now_filter(format_string):
        """当前时间过滤器"""
        return datetime.now(UTC).strftime(format_string)
    
    # 添加上传文件访问路由
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """处理上传文件的访问"""
        return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)
    
    # 添加请求日志记录
    @app.before_request
    def log_request():
        """记录请求信息"""
        app.logger.info(f'请求: {request.method} {request.url}')
        app.logger.debug(f'请求头: {dict(request.headers)}')
        if request.is_json:
            app.logger.debug(f'JSON数据: {request.get_json()}')
        elif request.form:
            app.logger.debug(f'表单数据: {dict(request.form)}')
    
    # 添加上下文处理器
    @app.context_processor
    def inject_now():
        """注入当前时间到模板"""
        return {'now': datetime.now(UTC)}
    
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
            app.logger.info('测试数据库初始化完成')
    
    @app.route('/csrf/refresh')
    def csrf_refresh():
        """刷新CSRF令牌"""
        return jsonify({'csrf_token': generate_csrf()})
    
    app.logger.info('应用初始化完成')
    return app
