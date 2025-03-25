"""
博客相关的控制器模块
"""

from flask import Blueprint

blog_bp = Blueprint('blog', __name__)

# 导入视图和评论模块
from . import views, comment

# 注册评论蓝图
blog_bp.register_blueprint(comment.comment_bp)

# 导出blog变量
blog = blog_bp