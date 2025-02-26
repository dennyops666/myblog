"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Role
from app.models.permission import Permission
from app.extensions import db
from app.services.user import UserService
from app.services.role_service import RoleService
from app.decorators import admin_required
from app.services.operation_log_service import OperationLogService
from app.forms.auth import RegisterForm
from flask import current_app
from flask_wtf.csrf import generate_csrf

user_bp = Blueprint('user', __name__)
user_service = UserService()
role_service = RoleService()
operation_log_service = OperationLogService()

@user_bp.route('/')
@login_required
@admin_required
def index():
    """用户列表页面"""
    page = request.args.get('page', 1, type=int)
    result = user_service.get_users(page=page)
    
    if result['status'] == 'success':
        return render_template('admin/user/list.html', 
                             users=result['users'],
                             pagination=result['pagination'])
    else:
        flash(result['message'], 'error')
        return render_template('admin/user/list.html', users=[], pagination=None)

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """创建用户"""
    form = RegisterForm()
    form.submit.label.text = '创建用户'  # 修改提交按钮文本
    
    try:
        roles = role_service.get_available_roles()
    except Exception as e:
        current_app.logger.error(f"获取角色列表失败: {str(e)}")
        error_message = '获取角色列表失败'
        return render_template('admin/user/create.html', form=form, roles=[], error=error_message)
    
    if request.method == 'POST':
        current_app.logger.info(f"接收到创建用户请求: {request.form}")
        try:
            # 手动验证表单
            if form.validate():
                current_app.logger.info("表单验证通过")
                # 获取表单数据
                username = form.username.data
                password = form.password.data
                email = form.email.data
                nickname = request.form.get('nickname')
                role_ids = request.form.getlist('roles')
                is_active = request.form.get('is_active') == 'on'
                
                current_app.logger.info(f"创建用户数据: username={username}, email={email}, nickname={nickname}, role_ids={role_ids}, is_active={is_active}")
                
                # 创建用户
                result = user_service.create_user(
                    username=username,
                    password=password,
                    email=email,
                    nickname=nickname,
                    role_ids=role_ids,
                    is_active=is_active
                )
                
                if result['status'] == 'success':
                    flash('用户创建成功', 'success')
                    return redirect(url_for('admin.user.index'))
                else:
                    return render_template('admin/user/create.html', form=form, roles=roles, error=result['message'])
            else:
                current_app.logger.warning(f"表单验证失败: {form.errors}")
                errors = []
                for field, field_errors in form.errors.items():
                    for error in field_errors:
                        errors.append(f'{getattr(form, field).label.text}: {error}')
                return render_template('admin/user/create.html', form=form, roles=roles, error=errors[0] if errors else None)
        except Exception as e:
            current_app.logger.error(f"创建用户失败: {str(e)}")
            return render_template('admin/user/create.html', form=form, roles=roles, error=str(e))
            
    return render_template('admin/user/create.html', form=form, roles=roles)

@user_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """编辑用户"""
    result = user_service.get_user(user_id)
    if result['status'] == 'error':
        flash(result['message'], 'error')
        return redirect(url_for('admin.user.index'))
        
    user = result['user']
    # 检查是否是超级管理员
    is_super_admin = any(role.permissions & Permission.SUPER_ADMIN.value for role in user.roles)
    
    # 创建表单实例并用用户数据填充
    form = RegisterForm(obj=user)
    form.submit.label.text = '更新用户'  # 修改提交按钮文本
    
    if request.method == 'POST':
        data = request.get_json() or request.form.to_dict()
        
        # 如果是超级管理员，不允许修改角色
        if is_super_admin and user_id == 1:
            if 'roles' in data:
                del data['roles']
                
        # 更新用户信息
        result = user_service.update_user(
            user_id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            nickname=data.get('nickname'),
            password=data.get('password') if data.get('password') else None,
            is_active=bool(data.get('is_active')),
            role_ids=[int(r) for r in request.form.getlist('roles')] if not is_super_admin or user_id != 1 else None
        )
        
        current_app.logger.info(f"更新结果: {result}")
        
        if result['status'] == 'success':
            # 记录操作日志
            operation_log_service.log_operation(
                user=current_user,
                action='更新用户',
                details=f'更新用户 {user.username} 的信息'
            )
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '用户更新成功',
                    'redirect_url': url_for('admin.user.index'),
                    'csrf_token': generate_csrf()
                })
            flash('用户更新成功', 'success')
            return redirect(url_for('admin.user.index'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': result['message']})
            flash(result['message'], 'error')
    
    roles = role_service.get_all_roles()
    return render_template('admin/user/edit.html', form=form, user=user, roles=roles, is_super_admin=is_super_admin)

@user_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """删除用户"""
    user = user_service.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})
        
    # 不允许删除超级管理员
    if user_id == 1:
        return jsonify({'success': False, 'message': '不能删除超级管理员账户'})
        
    # 不能删除自己
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': '不能删除当前登录的账户'})
    
    result = user_service.delete_user(user_id)
    
    if result['status'] == 'success':
        # 记录操作日志
        operation_log_service.log_operation(
            user=current_user,
            action='删除用户',
            details=f'删除用户 {user.username}'
        )
        return jsonify({'success': True, 'message': '用户删除成功'})
    else:
        return jsonify({'success': False, 'message': result['message']})

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