"""
文件名：__init__.py
描述：Flask应用初始化
作者：denny
创建日期：2025-02-16
"""

from flask import Flask, render_template
from flask_mail import Mail
from flask_wtf.csrf import CSRFError
from datetime import timedelta
from app.config import config
from app.extensions import db, migrate, login_manager, csrf

# 创建邮件扩展实例
mail = Mail()

def create_app(config_name='development'):
    """
    创建Flask应用实例
    
    Args:
        config_name (str): 配置名称，可选值：development, production, testing
        
    Returns:
        Flask: Flask应用实例
    """
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 配置会话
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 会话有效期7天
    app.config['SESSION_COOKIE_SECURE'] = True  # 仅通过HTTPS发送cookie
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # 防止JavaScript访问cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # 防止CSRF攻击
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # 配置CSRF保护
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', 
                             message='CSRF验证失败，请刷新页面重试。'), 400
    
    # 初始化自定义过滤器
    from app.utils.filters import init_filters
    init_filters(app)
    
    # 确保在测试环境中正确初始化数据库
    if config_name == 'testing':
        with app.app_context():
            db.drop_all()  # 清理现有数据
            db.create_all()  # 创建新的表
            db.session.commit()  # 提交更改
    
    # 配置登录视图
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '请先登录'
    login_manager.login_message_category = 'warning'
    
    # 注册蓝图
    from app.controllers.admin import admin_bp
    from app.controllers.blog import blog_bp
    from app.controllers.auth import auth_bp
    
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(blog_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # 注册命令
    from app.commands import create_admin, init_db
    app.cli.add_command(create_admin)
    app.cli.add_command(init_db)
    
    return app
