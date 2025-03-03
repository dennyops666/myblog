"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from flask_login import login_required, current_user
from app.models import User, Role
from app.models.permission import Permission
from app.extensions import db
from app.services.user import UserService
from app.services.role_service import RoleService
from app.decorators import admin_required
from app.services.operation_log_service import OperationLogService
from app.forms.auth import RegisterForm

bp = Blueprint('user', __name__)
user_service = UserService()
role_service = RoleService()
operation_log_service = OperationLogService()

@bp.route('/')
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
        return render_template('admin/user/list.html', users=[], pagination=None)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """创建用户"""
    try:
        form = RegisterForm()
        form.submit.label.text = '创建用户'  # 修改提交按钮文本
        
        # 获取可用角色列表
        roles = role_service.get_available_roles()
        
        if request.method == 'POST':
            # 获取表单数据
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')
            nickname = request.form.get('nickname')
            role_ids = request.form.getlist('roles')
            is_active = request.form.get('is_active') == 'on'
            
            # 创建用户
            result = user_service.create_user(
                username=username,
                password=password,
                email=email,
                nickname=nickname,
                role_ids=role_ids,
                is_active=is_active
            )
            
            # 记录操作日志
            if result['status']:
                operation_log_service.log_operation(
                    user=current_user,
                    action='创建用户',
                    details=f'创建用户 {username}'
                )
                
            # 直接返回服务层的结果
            return jsonify({
                'success': result['status'],
                'message': result['message'],
                'redirect_url': url_for('admin.user.index') if result['status'] else None
            })
                
        return render_template('admin/user/create.html', form=form, roles=roles)
        
    except Exception as e:
        current_app.logger.error(f"创建用户页面出错: {str(e)}")
        current_app.logger.exception(e)  # 记录完整的异常堆栈
        
        return jsonify({
            'success': False,
            'message': '系统错误，请稍后重试'
        })

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """编辑用户"""
    try:
        # 获取用户信息
        result = user_service.get_user(user_id)
        if not result['status']:
            if request.method == 'GET':
                form = RegisterForm(obj=result['user'])  # 创建表单对象
                return render_template('admin/user/edit.html', user=result['user'], form=form, error='用户不存在')
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
            
        user = result['user']
        
        # 不能编辑超级管理员
        if user.is_super_admin and not current_user.is_super_admin:
            if request.method == 'GET':
                form = RegisterForm(obj=user)  # 创建表单对象
                return render_template('admin/user/edit.html', user=user, form=form, error='没有权限编辑超级管理员')
            return jsonify({
                'success': False,
                'message': '没有权限编辑超级管理员'
            })
            
        # 获取所有角色
        roles = role_service.get_available_roles()
        
        if request.method == 'POST':
            # 创建表单对象并加载数据
            form = RegisterForm(formdata=request.form, obj=user)
            
            # 获取表单数据
            username = request.form.get('username')
            email = request.form.get('email')
            nickname = request.form.get('nickname', '')
            password = request.form.get('password', '')
            is_active = request.form.get('is_active') == 'on'
            role_ids = request.form.getlist('roles')
            
            # 过滤掉超级管理员角色
            if not current_user.is_super_admin:
                super_admin_role = role_service.get_role_by_name('super_admin')
                if super_admin_role and str(super_admin_role.id) in role_ids:
                    role_ids.remove(str(super_admin_role.id))
            
            # 验证表单
            if form.validate():
                # 更新用户信息
                result = user_service.update_user(
                    user_id=user_id,
                    username=username,
                    email=email,
                    nickname=nickname,
                    password=password,
                    is_active=is_active,
                    role_ids=role_ids
                )
                
                if result['status']:
                    # 记录操作日志
                    operation_log_service.log_operation(
                        user=current_user,
                        action='编辑用户',
                        details=f'编辑用户 {username}'
                    )
                    return jsonify({
                        'success': True,
                        'message': '保存成功',
                        'redirect_url': url_for('admin.user.index')
                    })
                else:
                    return jsonify({
                        'success': False,
                        'message': result['message']
                    })
            else:
                # 处理密码验证错误
                if hasattr(form, '_password_invalid'):
                    return jsonify({
                        'success': False,
                        'message': '长度至少6位，必须包含字母和数字'
                    })
                elif hasattr(form, '_password_mismatch'):
                    return jsonify({
                        'success': False,
                        'message': '两次输入的密码不一致'
                    })
                
                # 处理其他字段的验证错误
                for field, errors in form.errors.items():
                    if field not in ['password', 'password2']:
                        return jsonify({
                            'success': False,
                            'message': errors[0]
                        })
                
                return jsonify({
                    'success': False,
                    'message': '表单验证失败'
                })
        
        # GET请求，创建表单对象
        form = RegisterForm(obj=user)
        # 返回编辑页面
        return render_template('admin/user/edit.html', user=user, roles=roles, form=form)
        
    except Exception as e:
        current_app.logger.error(f'编辑用户出错: {str(e)}')
        current_app.logger.exception(e)  # 记录完整的异常堆栈
        if request.method == 'GET':
            return render_template('admin/user/edit.html', error='系统错误，请稍后重试')
        return jsonify({
            'success': False,
            'message': '系统错误，请稍后重试'
        })

@bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """删除用户"""
    try:
        # 检查用户是否存在
        result = user_service.get_user(user_id)
        if not result['status']:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            })
            
        user = result['user']
        
        # 不能删除超级管理员
        if user.is_super_admin:
            return jsonify({
                'success': False,
                'message': '不能删除超级管理员'
            })
            
        # 不能删除当前登录用户
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'message': '不能删除当前登录用户'
            })
            
        # 删除用户
        result = user_service.delete_user(user_id)
        if result['status']:
            # 记录操作日志
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=f'删除用户 {user.username}'
            )
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            })
        
    except Exception as e:
        current_app.logger.error(f"删除用户失败: {str(e)}")
        current_app.logger.exception(e)  # 记录完整的异常堆栈
        return jsonify({
            'success': False,
            'message': '删除用户失败'
        })

@bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not all([old_password, new_password, confirm_password]):
        return jsonify({
            'success': False,
            'message': '请填写所有必填字段'
        })
        
    if new_password != confirm_password:
        return jsonify({
            'success': False,
            'message': '两次输入的密码不一致'
        })
        
    try:
        user_service.change_password(
            current_user.id,
            old_password,
            new_password
        )
        return jsonify({
            'success': True,
            'message': '密码修改成功，请重新登录'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }) 