"""
文件名：__init__.py
描述：管理后台蓝图初始化
作者：denny
"""

from flask import Blueprint, redirect, url_for

admin = Blueprint('admin_main', __name__)

# 添加测试路由
@admin.route('/')
def index():
    """管理后台首页重定向，已废弃，改用admin_dashboard蓝图"""
    return redirect(url_for('admin_dashboard.dashboard'))

# 导入视图，确保路由被注册
from app.admin import views 