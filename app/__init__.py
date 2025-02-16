"""
文件名：__init__.py
描述：Flask应用初始化
作者：denny
创建日期：2025-02-16
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import config

# 创建扩展实例
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

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
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
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
    app.register_blueprint(auth_bp)
    
    # 注册命令
    from app.commands import create_admin, init_db
    app.cli.add_command(create_admin)
    app.cli.add_command(init_db)
    
    return app
