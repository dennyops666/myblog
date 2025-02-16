"""
文件名：__init__.py
描述：控制器包初始化
作者：denny
创建日期：2025-02-16
"""

from .admin import admin_bp
from .blog import blog_bp

__all__ = ['admin_bp', 'blog_bp']
