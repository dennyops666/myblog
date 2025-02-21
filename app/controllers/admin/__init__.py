"""
文件名：__init__.py
描述：管理后台蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from flask_login import current_user, logout_user, login_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
def check_auth():
    """检查认证状态"""
    if not current_user.is_authenticated:
        return jsonify({'error': '未授权访问'}), 401

@admin_bp.route('/')
def index():
    """管理后台首页"""
    return render_template('admin/index.html')

@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """退出登录"""
    logout_user()
    return redirect(url_for('auth.login'))

# 导入其他视图
from . import post, user, comment, category, tag
