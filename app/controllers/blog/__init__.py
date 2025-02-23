"""
文件名：__init__.py
描述：博客控制器初始化
作者：denny
创建日期：2024-03-21
"""

from app.middleware.security import csrf_protect, xss_protect, sql_injection_protect
from .views import blog_bp

# 为所有视图添加安全装饰器
for endpoint, view_func in blog_bp.view_functions.items():
    blog_bp.view_functions[endpoint] = csrf_protect()(
        xss_protect()(
            sql_injection_protect()(view_func)
        )
    )
