"""
文件名：__init__.py
描述：管理后台蓝图初始化
作者：denny
创建日期：2025-02-16
"""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__)

# 导入视图
from . import user, post, comment, index
