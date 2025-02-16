"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService
from . import admin_bp

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = UserService.get_user_by_username(username)
        if user and user.verify_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('admin.index'))
        flash('用户名或密码错误', 'danger')
    
    return render_template('admin/user/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    logout_user()
    flash('已退出登录', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人信息维护"""
    if request.method == 'POST':
        email = request.form.get('email')
        
        try:
            UserService.update_user(current_user, email=email)
            flash('个人信息更新成功', 'success')
        except Exception as e:
            flash(f'更新失败：{str(e)}', 'danger')
    
    return render_template('admin/user/profile.html')

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码"""
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.verify_password(old_password):
            flash('原密码错误', 'danger')
        elif new_password != confirm_password:
            flash('两次输入的新密码不一致', 'danger')
        elif len(new_password) < 6:
            flash('新密码长度不能小于6个字符', 'danger')
        else:
            try:
                UserService.update_user(current_user, password=new_password)
                flash('密码修改成功，请重新登录', 'success')
                return redirect(url_for('admin.logout'))
            except Exception as e:
                flash(f'修改失败：{str(e)}', 'danger')
    
    return render_template('admin/user/change_password.html') 