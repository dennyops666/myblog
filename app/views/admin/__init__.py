"""
文件名：__init__.py
描述：管理后台蓝图
作者：denny
"""

from flask import Blueprint

# 创建主蓝图
admin_bp = Blueprint('admin_dashboard', __name__, url_prefix='/admin')

# 导入并注册用户管理蓝图
from app.views.admin.user import bp as user_bp
admin_bp.register_blueprint(user_bp, url_prefix='/user')

# 用于主模块导入
bp = admin_bp

# 初始化函数，记录蓝图注册信息
def init_app(app):
    app.register_blueprint(admin_bp)
    app.logger.info("=== 管理后台蓝图注册 ===")
    app.logger.info(f"主蓝图: {admin_bp.name}, URL前缀: {admin_bp.url_prefix}")
    app.logger.info(f"用户蓝图: {user_bp.name}, URL前缀: '/admin/user'")
    app.logger.info("已注册路由:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule):
            app.logger.info(f"{rule.endpoint}: {rule}")
