"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services import UserService
from . import admin_bp

user_service = UserService()

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料页面"""
    if request.method == 'POST':
        data = {
            'nickname': request.form.get('nickname'),
            'email': request.form.get('email')
        }
        
        result = user_service.update_user(current_user.id, data)
        if result['status'] == 'success':
            flash('个人资料更新成功', 'success')
            return redirect(url_for('admin.profile'))
        else:
            flash(result['message'], 'danger')
            
    return render_template('admin/user/profile.html')

@admin_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([old_password, new_password, confirm_password]):
        flash('请填写所有必填字段', 'danger')
        return redirect(url_for('admin.profile'))
        
    if new_password != confirm_password:
        flash('两次输入的密码不一致', 'danger')
        return redirect(url_for('admin.profile'))
        
    result = user_service.change_password(
        current_user.id,
        old_password,
        new_password
    )
    
    if result['status'] == 'success':
        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('auth.logout'))
    else:
        flash(result['message'], 'danger')
        return redirect(url_for('admin.profile')) 