"""
文件名：__init__.py
描述：认证蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService
from app.models import User
from app.forms.auth import LoginForm
from urllib.parse import urlparse
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import traceback

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    try:
        if current_user.is_authenticated:
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'success': True, 
                    'message': '已登录',
                    'csrf_token': generate_csrf()
                })
            return redirect(url_for('admin.index'))

        if request.method == 'GET':
            current_app.logger.debug('访问登录页面')
            form = LoginForm()
            response = make_response(render_template('auth/login.html', form=form))
            response.headers['X-CSRF-Token'] = generate_csrf()
            return response

        current_app.logger.debug(f'处理登录请求: {request.form}')
        form = LoginForm()
        
        if form.validate_on_submit():
            current_app.logger.debug(f'表单验证通过，用户名: {form.username.data}')
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data):
                if not user.is_active:
                    current_app.logger.warning(f'用户 {user.username} 已被禁用')
                    flash('账户已被禁用', 'error')
                    return redirect(url_for('login'))
                
                login_user(user, remember=form.remember_me.data)
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('admin.index')
                
                current_app.logger.info(f'用户 {user.username} 登录成功')
                response = redirect(next_page)
                response.headers['X-CSRF-Token'] = generate_csrf()
                return response
            
            current_app.logger.warning(f'登录失败，用户名: {form.username.data}')
            flash('用户名或密码错误', 'error')
            return redirect(url_for('login'))
        
        current_app.logger.warning(f'表单验证失败: {form.errors}')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{getattr(form, field).label.text}: {error}', 'error')
        return redirect(url_for('login'))
        
    except Exception as e:
        current_app.logger.error(f'登录过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        flash('服务器内部错误', 'error')
        return render_template('errors/500.html'), 500

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