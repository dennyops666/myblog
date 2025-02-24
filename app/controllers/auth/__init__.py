"""
文件名：__init__.py
描述：认证蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService
from app.models import User
from app.forms.auth import LoginForm
from urllib.parse import urlparse
from flask_wtf.csrf import generate_csrf

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if current_user.is_authenticated:
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True, 
                'message': '已登录',
                'csrf_token': generate_csrf()
            })
        return redirect(url_for('admin.index'))

    if request.method == 'GET':
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True,
                'message': '请登录',
                'csrf_token': generate_csrf()
            })
        return render_template('auth/login.html', form=LoginForm())

    if request.is_json:
        form = LoginForm.from_json(request.get_json())
    else:
        form = LoginForm()

    if form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                next_page = url_for('admin.index')
            
            if request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'next': next_page,
                    'csrf_token': generate_csrf()
                })
            return redirect(next_page)
        
        if request.is_json or request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': False,
                'message': '用户名或密码错误',
                'csrf_token': generate_csrf()
            }), 401
        flash('用户名或密码错误', 'error')
        return redirect(url_for('auth.login'))
    
    if request.is_json or request.headers.get('Accept') == 'application/json':
        return jsonify({
            'success': False,
            'message': '表单验证失败',
            'errors': form.errors,
            'csrf_token': generate_csrf()
        }), 400
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{getattr(form, field).label.text}: {error}', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """登出"""
    logout_user()
    if request.is_json:
        return jsonify({
            'success': True,
            'message': '已安全退出',
            'csrf_token': generate_csrf()
        })
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login'))