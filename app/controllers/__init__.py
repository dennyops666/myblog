"""
文件名：__init__.py
描述：控制器初始化
作者：denny
创建日期：2025-02-16
"""

from .admin import admin_bp
from .auth import auth_bp
from .blog import blog_bp

# 注册所有蓝图
def register_blueprints(app):
    """注册所有蓝图"""
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(blog_bp)

__all__ = ['admin_bp', 'auth_bp', 'blog_bp']
