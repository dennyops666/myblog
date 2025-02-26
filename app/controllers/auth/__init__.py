"""
文件名：__init__.py
描述：认证蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService, OperationLogService
from app.models import User, Permission
from app.forms.auth import LoginForm
from urllib.parse import urlparse
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import traceback

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理后台登录视图"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = user_service.get_user_by_username(form.username.data)
        
        if user and user.verify_password(form.password.data):
            # 检查是否具有管理员权限
            is_admin = False
            for role in user.roles:
                if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                    is_admin = True
                    break
                    
            if not is_admin:
                flash('您不是管理员，请从博客首页登录', 'danger')
                return redirect(url_for('blog.login'))
                
            # 管理员登录成功
            login_user(user, remember=form.remember_me.data)
            OperationLogService.log_operation(
                user=user,
                action='admin_login',
                details=f'管理员 {user.username} 登录后台'
            )
            flash('登录成功', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('admin.index'))
        else:
            flash('用户名或密码错误', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """登出"""
    try:
        user = current_user.username
        logout_user()
        current_app.logger.info(f'用户 {user} 已登出')
        if request.is_json:
            return jsonify({
                'success': True,
                'message': '已安全退出',
                'csrf_token': generate_csrf()
            })
        flash('已安全退出', 'success')
        return redirect(url_for('auth.login'))
    except Exception as e:
        current_app.logger.error(f'登出过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        if request.is_json:
            return jsonify({
                'success': False,
                'message': '服务器内部错误',
                'csrf_token': generate_csrf()
            }), 500
        flash('服务器内部错误', 'error')
        return render_template('errors/500.html'), 500