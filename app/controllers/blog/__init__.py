"""
文件名：__init__.py
描述：博客蓝图
作者：denny
创建日期：2025-02-16
"""

from flask import Blueprint

blog_bp = Blueprint('blog', __name__)

# 导入视图
from . import views
