"""
文件名：__init__.py
描述：控制器初始化
作者：denny
创建日期：2025-02-16
"""

# 空的初始化文件，避免循环导入

from flask import Blueprint
from app.controllers.auth import auth_bp
from app.controllers.blog import blog

# 注册所有蓝图
def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(blog)

__all__ = ['auth_bp', 'blog']
