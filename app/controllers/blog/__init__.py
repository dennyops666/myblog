"""
文件名：__init__.py
描述：博客控制器初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint
from app.middleware.security import xss_protect, sql_injection_protect
from app.services import UserService

blog_bp = Blueprint('blog', __name__)

# 为所有视图函数添加安全保护
for endpoint in blog_bp.view_functions:
    blog_bp.view_functions[endpoint] = xss_protect()(
        sql_injection_protect()(blog_bp.view_functions[endpoint])
    )

from . import views

user_service = UserService()
