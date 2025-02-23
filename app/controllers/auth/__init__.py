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
from app.forms.auth import LoginForm
from urllib.parse import urlparse

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    form = LoginForm()
    next_page = request.args.get('next')
    
    if request.method == 'POST':
        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                login_user(user, remember=form.remember_me.data)
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('admin.index')
                return redirect(next_page)
            flash('用户名或密码错误', 'error')
            return redirect(url_for('auth.login'))
        flash('表单验证失败', 'error')
        return redirect(url_for('auth.login'))
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """登出"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login'))