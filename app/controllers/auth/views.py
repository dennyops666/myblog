"""
文件名：views.py
描述：认证视图
作者：denny
创建日期：2025-02-16
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import safe_str_cmp
from app.models import User
from app.services import UserService
from app.forms import LoginForm, RegisterForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = UserService.get_user_by_username(form.username.data)
            if user is None or not user.verify_password(form.password.data):
                flash('用户名或密码错误', 'danger')
                return render_template('auth/login.html', form=form), 401
                
            if user.status == 0:
                flash('账号已被禁用', 'danger')
                return render_template('auth/login.html', form=form), 403
                
            # 登录用户
            login_user(user, remember=form.remember_me.data)
            
            # 获取下一个页面的 URL
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('admin.index')
                
            return redirect(next_page)
        except Exception as e:
            flash('登录失败，请稍后重试', 'danger')
            return render_template('auth/login.html', form=form), 500
            
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('blog.index'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # 检查用户名和邮箱是否已存在
            if UserService.get_user_by_username(form.username.data):
                flash('用户名已存在', 'danger')
                return render_template('auth/register.html', form=form), 400
                
            if UserService.get_user_by_email(form.email.data):
                flash('邮箱已被注册', 'danger')
                return render_template('auth/register.html', form=form), 400
            
            # 创建新用户
            user = UserService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            flash('注册成功，请登录', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('注册失败，请稍后重试', 'danger')
            return render_template('auth/register.html', form=form), 500
            
    return render_template('auth/register.html', form=form)