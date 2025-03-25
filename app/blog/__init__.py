"""
文件名：__init__.py
描述：博客蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint

blog = Blueprint('blog', __name__)

from app.blog import views 