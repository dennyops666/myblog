"""
文件名：__init__.py
描述：认证蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService
from app.models import User

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not all([username, password]):
            flash('请填写所有必填字段', 'danger')
            return render_template('admin/login.html'), 200
            
        user = user_service.get_user_by_username(username)
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('登录成功', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('admin.index'))
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('admin/login.html'), 200
            
    return render_template('admin/login.html')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login'))