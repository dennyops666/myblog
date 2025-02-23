"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.services import UserService
from app.extensions import db

user_bp = Blueprint('user', __name__, url_prefix='/users')
user_service = UserService()

@user_bp.route('/')
@login_required
def index():
    """用户列表页面"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    result = user_service.get_users(page=page, per_page=per_page)
    return render_template('admin/user/list.html', users=result['users'])

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建用户"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        try:
            user = user_service.create_user(
                username=username,
                password=password,
                email=email
            )
            flash('用户创建成功', 'success')
            return redirect(url_for('admin.user.index'))
        except Exception as e:
            flash(str(e), 'error')
            
    return render_template('admin/user/create.html')

@user_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(user_id):
    """编辑用户"""
    user = user_service.get_user_by_id(user_id)
    if not user:
        flash('用户不存在', 'error')
        return redirect(url_for('admin.user.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user_service.update_user(
                user_id=user_id,
                username=username,
                email=email,
                password=password
            )
            flash('用户更新成功', 'success')
            return redirect(url_for('admin.user.index'))
        except Exception as e:
            flash(str(e), 'error')
            
    return render_template('admin/user/edit.html', user=user)

@user_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
def delete(user_id):
    """删除用户"""
    try:
        user_service.delete_user(user_id)
        flash('用户删除成功', 'success')
    except Exception as e:
        flash(str(e), 'error')
        
    return redirect(url_for('admin.user.index'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user_service.update_user(
                user_id=current_user.id,
                username=username,
                email=email,
                password=password
            )
            flash('个人资料更新成功', 'success')
            return redirect(url_for('admin.user.profile'))
        except Exception as e:
            flash(str(e), 'error')
            
    return render_template('admin/user/profile.html', user=current_user)

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([old_password, new_password, confirm_password]):
        flash('请填写所有必填字段', 'danger')
        return redirect(url_for('admin.user.profile'))
        
    if new_password != confirm_password:
        flash('两次输入的密码不一致', 'danger')
        return redirect(url_for('admin.user.profile'))
        
    try:
        user_service.change_password(
            current_user.id,
            old_password,
            new_password
        )
        flash('密码修改成功，请重新登录', 'success')
        return redirect(url_for('admin.logout'))
    except Exception as e:
        flash(str(e), 'danger')
        return redirect(url_for('admin.user.profile')) 