"""
文件名：user.py
描述：用户管理控制器
作者：denny
创建日期：2024-03-21
"""

import re
import traceback
from typing import Dict, List, Optional, Union
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

from app.models import User, Role
from app.models.permission import Permission
from app.extensions import db
from app.services.user import UserService
from app.services.role_service import RoleService
from app.decorators import admin_required
from app.services.operation_log import operation_log_service
from app.forms.auth import RegisterForm
from app.utils.response import ApiResponse
from app.utils.logging import log_error, log_info, log_warning
from app.utils.validation import validate_email, validate_username

# 初始化蓝图和服务
user_bp = Blueprint('user', __name__)
user_service = UserService()
role_service = RoleService()

# 定义错误信息
ERROR_MESSAGES = {
    'user_not_found': '用户不存在',
    'permission_denied': '没有权限执行此操作',
    'invalid_request': '无效的请求',
    'system_error': '系统错误，请稍后重试',
    'validation_error': '表单验证错误',
    'database_error': '数据库操作错误'
}

def has_delete_permission(current_user: User, target_user_id: int) -> bool:
    """检查当前用户是否有权限删除目标用户
    
    Args:
        current_user: 当前登录用户
        target_user_id: 要删除的目标用户ID
        
    Returns:
        bool: 是否有权限删除
        
    Raises:
        ValueError: 当目标用户ID无效时抛出
        PermissionError: 当权限检查失败时抛出
    """
    try:
        # 检查目标用户ID是否有效
        if not isinstance(target_user_id, int) or target_user_id <= 0:
            raise ValueError(f'无效的用户ID: {target_user_id}')
        
        # 获取目标用户
        target_user = user_service.get_user_by_id(target_user_id)
        if not target_user:
            log_warning(
                '目标用户不存在',
                extra={
                    'current_user_id': current_user.id,
                    'target_user_id': target_user_id,
                    'action': 'check_delete_permission',
                    'status': 'warning'
                }
            )
            return False
        
        # 添加调试日志：输出target_user和current_user信息
        current_app.logger.debug(f'目标用户：ID={target_user.id}, 用户名={target_user.username}, 是管理员={target_user.is_admin_user}')
        current_app.logger.debug(f'当前用户：ID={current_user.id}, 用户名={current_user.username}, 是管理员={current_user.is_admin_user}')
        
        # 检查用户是否有super_admin角色
        has_super_admin_role = False
        if hasattr(target_user, 'roles'):
            for role in target_user.roles:
                if role.name == 'super_admin':
                    has_super_admin_role = True
                    current_app.logger.debug(f'用户 {target_user.username} 拥有超级管理员角色')
                    break
        
        # 如果用户是管理员用户或者有超级管理员角色，不允许删除
        if target_user.username == 'admin' or target_user.is_admin_user or has_super_admin_role:
            current_app.logger.debug(f'不能删除超级管理员或管理员用户: {target_user.username}')
            return False
        
        # 始终允许删除非管理员用户
        current_app.logger.debug(f'允许删除普通用户: {target_user.username}')
        return True
        
    except ValueError as e:
        log_error(
            str(e),
            extra={
                'current_user_id': current_user.id,
                'target_user_id': target_user_id,
                'error_type': 'ValueError',
                'action': 'check_delete_permission',
                'status': 'error'
            }
        )
        raise
        
    except Exception as e:
        log_error(
            f'检查删除权限时发生错误: {str(e)}',
            extra={
                'current_user_id': current_user.id,
                'target_user_id': target_user_id,
                'error_type': type(e).__name__,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'action': 'check_delete_permission',
                'status': 'error'
            }
        )
        raise PermissionError('检查删除权限时发生错误') from e

@user_bp.route('/')
@login_required
@admin_required
def index():
    """用户列表页面
    
    Returns:
        flask.Response: 渲染后的用户列表页面
    """
    try:
        from app.models import User, Role
        
        # 直接从数据库获取所有用户
        all_users = User.query.all()
        current_app.logger.info(f'获取到 {len(all_users)} 个用户')
        
        # 获取统计信息
        stats = {
            'total': len(all_users),
            'active': sum(1 for u in all_users if u.is_active),
            'inactive': sum(1 for u in all_users if not u.is_active)
        }
        
        # 获取可用角色
        roles = Role.query.all()
        
        # 记录操作日志
        operation_log_service.log_operation(
            user=current_user,
            action='查看用户列表',
            details=f'成功查看用户列表，共 {len(all_users)} 个用户',
            result='success'
        )
        
        # 返回模板
        return render_template(
            'admin/user/list.html',
            users=all_users,
            stats=stats,
            roles=roles,
            pagination=None
        )
    except Exception as e:
        current_app.logger.error(f'获取用户列表时发生错误: {str(e)}')
        current_app.logger.exception(e)
        
        # 记录操作日志
        operation_log_service.log_operation(
            user=current_user,
            action='查看用户列表',
            details=f'获取用户列表失败: {str(e)}',
            result='error'
        )
        
        # 返回错误页面
        return render_template(
            'admin/error.html',
            error='获取用户列表失败',
            error_code=500,
            show_debug_info=current_app.debug,
            error_details={
                'message': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc() if current_app.debug else None
            },
            suggestion='请稍后重试或联系管理员'
        ), 500

@user_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """创建新用户
    
    Returns:
        flask.Response: 渲染后的创建用户页面或操作结果
        
    Raises:
        ValueError: 当表单数据验证失败时抛出
        PermissionError: 当权限不足时抛出
        SQLAlchemyError: 当数据库操作失败时抛出
    """
    try:
        # 获取角色列表
        try:
            # 使用角色服务获取可用角色（已排除超级管理员角色，除非当前用户是超级管理员）
            roles = role_service.get_available_roles()
            
            # 记录访问日志
            log_info(
                f'用户 {current_user.username} 访问创建用户页面',
                extra={
                    'user_id': current_user.id,
                    'method': request.method,
                    'action': 'access_create_user_page',
                    'status': 'success'
                }
            )
        except Exception as e:
            log_error(
                f'获取角色列表失败: {str(e)}',
                extra={
                    'user_id': current_user.id,
                    'error_type': 'SQLAlchemyError',
                    'error': str(e),
                    'traceback': traceback.format_exc(),
                    'action': 'load_create_user_page',
                    'status': 'error'
                }
            )
            
            return jsonify(ApiResponse.error(
                message=ERROR_MESSAGES['database_error'],
                error_details=str(e) if current_app.debug else None
            )), 500
        
        # 初始化表单
        form = RegisterForm()
        form.submit.label.text = '创建用户'
        
        if request.method == 'GET':
            try:                
                # 记录成功日志
                log_info(
                    f'成功加载创建用户页面',
                    extra={
                        'user_id': current_user.id,
                        'available_roles': len(roles),
                        'action': 'load_create_user_page',
                        'status': 'success'
                    }
                )
                
                return render_template('admin/user/create.html', form=form, roles=roles)
                
            except SQLAlchemyError as e:
                # 记录数据库错误
                log_error(
                    f'获取角色列表失败: {str(e)}',
                    extra={
                        'user_id': current_user.id,
                        'error_type': 'SQLAlchemyError',
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'action': 'load_create_user_page',
                        'status': 'error'
                    }
                )
                
                return jsonify(ApiResponse.error(
                    message=ERROR_MESSAGES['database_error'],
                    error_details=str(e) if current_app.debug else None
                )), 500
        
        if request.method == 'POST':
            try:
                # 创建表单对象以便在验证失败时重新渲染
                form = RegisterForm(obj=user)
                
                # 获取表单数据
                username = request.form.get('username')
                email = request.form.get('email')
                nickname = request.form.get('nickname', '')
                password = request.form.get('password', '')
                is_active = request.form.get('is_active') == 'on'
                role_ids = request.form.getlist('roles')
                
                # 检查是否尝试创建超级管理员
                super_admin_role = Role.query.filter_by(name='super_admin').first()
                
                # 安全检查：如果不是超级管理员但尝试分配超级管理员角色，直接移除该角色
                if super_admin_role and current_user.username != 'admin':
                    # 如果尝试选择超级管理员角色，那么移除它
                    if str(super_admin_role.id) in role_ids:
                        role_ids.remove(str(super_admin_role.id))
                        current_app.logger.warning(
                            f'用户 {current_user.username} 尝试分配超级管理员角色，已自动移除',
                            extra={
                                'user_id': current_user.id,
                                'action': 'filter_super_admin_role',
                                'status': 'warning'
                            }
                        )
                
                # 记录创建尝试
                log_info(
                    f'用户 {current_user.username} 尝试创建新用户',
                    extra={
                        'user_id': current_user.id,
                        'form_data': {
                            **form_data,
                            'password': '******'  # 隐藏密码
                        },
                        'action': 'attempt_create_user',
                        'status': 'pending'
                    }
                )
                
                # 验证表单数据
                validation_errors = []
                
                if not username:
                    validation_errors.append('用户名不能为空')
                elif not validate_username(username):
                    validation_errors.append('用户名格式不正确')
                    
                if not password:
                    validation_errors.append('密码不能为空')
                elif len(password) < 8:
                    validation_errors.append('密码长度不能少于8个字符')
                    
                if not email:
                    validation_errors.append('邮箱地址不能为空')
                elif not validate_email(email):
                    validation_errors.append('邮箱地址格式不正确')
                    
                if not role_ids:
                    validation_errors.append('请至少选择一个角色')
                
                if validation_errors:
                    # 记录验证错误
                    log_warning(
                        '表单验证失败',
                        extra={
                            'user_id': current_user.id,
                            'validation_errors': validation_errors,
                            'form_data': {
                                **form_data,
                                'password': '******'
                            },
                            'action': 'validate_create_user_form',
                            'status': 'warning'
                        }
                    )
                    
                    # 不再返回JSON响应，而是使用flash消息并重新渲染页面
                    for error in validation_errors:
                        flash(error, 'danger')
                    return render_template('admin/user/create.html', form=form, roles=roles)
                
                # 创建用户
                result = user_service.create_user(**form_data)
                
                if result['status']:
                    # 记录成功日志
                    log_info(
                        f'成功创建用户 {form_data["username"]}',
                        extra={
                            'user_id': current_user.id,
                            'new_user': {
                                'username': form_data['username'],
                                'email': form_data['email'],
                                'roles': form_data['role_ids'],
                                'is_active': form_data['is_active']
                            },
                            'action': 'create_user',
                            'status': 'success'
                        }
                    )
                    
                    # 记录操作日志
                    operation_log_service.log_operation(
                        user=current_user,
                        action='创建用户',
                        details=f'成功创建用户 {form_data["username"]}',
                        result='success'
                    )
                    
                    # 使用flash消息并重定向，而不是返回JSON
                    flash('用户创建成功', 'success')
                    return redirect(url_for('admin_dashboard.user.index'))
                else:
                    # 记录失败日志
                    log_warning(
                        f'创建用户失败: {result["message"]}',
                        extra={
                            'user_id': current_user.id,
                            'error': result['message'],
                            'form_data': {
                                **form_data,
                                'password': '******'
                            },
                            'action': 'create_user',
                            'status': 'failure'
                        }
                    )
                    
                    # 记录操作日志
                    operation_log_service.log_operation(
                        user=current_user,
                        action='创建用户',
                        details=f'创建用户失败: {result["message"]}',
                        result='failure'
                    )
                    
                    # 使用flash消息并重新渲染页面，而不是返回JSON
                    flash(result['message'], 'danger')
                    return render_template('admin/user/create.html', form=form, roles=roles)
                    
            except ValueError as e:
                # 记录验证错误
                log_warning(
                    str(e),
                    extra={
                        'user_id': current_user.id,
                        'error_type': 'ValueError',
                        'error': str(e),
                        'form_data': {
                            **form_data,
                            'password': '******'
                        },
                        'action': 'create_user',
                        'status': 'warning'
                    }
                )
                
                # 记录操作日志
                operation_log_service.log_operation(
                    user=current_user,
                    action='创建用户',
                    details=f'验证错误: {str(e)}',
                    result='warning'
                )
                
                # 使用flash消息并重新渲染页面，而不是返回JSON
                flash(str(e), 'danger')
                return render_template('admin/user/create.html', form=form, roles=roles)
                
            except SQLAlchemyError as e:
                # 记录数据库错误
                log_error(
                    f'创建用户时数据库错误: {str(e)}',
                    extra={
                        'user_id': current_user.id,
                        'error_type': 'SQLAlchemyError',
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'form_data': {
                            **form_data,
                            'password': '******'
                        },
                        'action': 'create_user',
                        'status': 'error'
                    }
                )
                
                # 记录操作日志
                operation_log_service.log_operation(
                    user=current_user,
                    action='创建用户',
                    details=f'数据库错误: {str(e)}',
                    result='error'
                )
                
                # 使用flash消息并重新渲染页面，而不是返回JSON
                flash('数据库操作错误，请稍后重试', 'danger')
                return render_template('admin/user/create.html', form=form, roles=roles)
                
            except Exception as e:
                # 记录未预期的错误
                log_error(
                    f'创建用户时发生未预期的错误: {str(e)}',
                    extra={
                        'user_id': current_user.id,
                        'error_type': type(e).__name__,
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'form_data': {
                            **form_data,
                            'password': '******'
                        },
                        'action': 'create_user',
                        'status': 'error'
                    }
                )
                
                # 记录操作日志
                operation_log_service.log_operation(
                    user=current_user,
                    action='创建用户',
                    details=f'系统错误: {str(e)}',
                    result='error'
                )
                
                # 使用flash消息并重新渲染页面，而不是返回JSON
                flash('系统错误，请稍后重试', 'danger')
                return render_template('admin/user/create.html', form=form, roles=roles)
                
    except Exception as e:
        # 记录未预期的错误
        log_error(
            f'访问或处理创建用户页面时发生未预期的错误: {str(e)}',
            extra={
                'user_id': current_user.id,
                'error_type': type(e).__name__,
                'error': str(e),
                'traceback': traceback.format_exc(),
                'method': request.method,
                'action': 'create_user_page',
                'status': 'error'
            }
        )
        
        # 记录操作日志
        operation_log_service.log_operation(
            user=current_user,
            action='创建用户',
            details={
                'error': str(e),
                'error_type': 'system_error',
                'method': request.method,
                'traceback': traceback.format_exc() if current_app.debug else None
            },
            result='error'
        )
        
        # 使用flash消息并重新渲染错误页面，而不是返回JSON
        return render_template('admin/error.html',
            error='系统错误，无法完成用户创建操作',
            error_code=500,
            show_debug_info=current_app.debug,
            error_details={
                'message': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc() if current_app.debug else None
            },
            suggestion='请稍后重试或联系管理员'
        ), 500

@user_bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """编辑用户"""
    user = None  # 预先定义user变量，防止在异常处理中引用未定义变量
    try:
        # 获取用户
        user = User.query.get_or_404(user_id)
        
        # 判断用户是否有权限编辑
        if not current_user.is_super_admin and user.is_super_admin:
            current_app.logger.warning(
                f'用户 {current_user.username} 尝试编辑超级管理员 {user.username}',
                extra={
                    'user_id': current_user.id,
                    'target_user': user.username,
                    'action': 'edit_user_unauthorized',
                    'status': 'forbidden'
                }
            )
            operation_log_service.log_operation(
                user=current_user,
                action='编辑用户',
                details=f'无权编辑超级管理员 {user.username}',
                result='forbidden'
            )
            # 使用flash消息和重定向替代JSON响应
            flash('您没有权限编辑超级管理员用户', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 获取所有角色，排除特殊角色
        roles = []
        
        # 如果是超级管理员用户，只能有超级管理员角色
        if user.is_admin_user:
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            if super_admin_role:
                roles = [super_admin_role]
        else:
            # 普通用户可以分配普通角色，排除超级管理员角色
            roles = Role.query.filter(Role.name != 'super_admin').all()
            current_app.logger.debug(f"获取到 {len(roles)} 个可用角色用于编辑用户")
        
        if request.method == 'GET':
            current_app.logger.info(f'用户 {current_user.username} 访问编辑用户页面 - 用户: {user.username}')
            # 获取用户统计信息，直接从用户对象获取
            try:
                stats = {
                    'posts_count': len(user.posts) if hasattr(user, 'posts') else 0,
                    'comments_count': user.comments.count() if hasattr(user, 'comments') else 0,
                    'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                    'is_active': user.is_active,
                    'last_login': getattr(user, 'last_login', None),
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            except Exception as e:
                current_app.logger.warning(f'获取用户统计信息失败: {str(e)}')
                stats = {
                    'posts_count': 0,
                    'comments_count': 0,
                    'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                    'is_active': user.is_active,
                    'last_login': getattr(user, 'last_login', None),
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
            
            # 获取用户最近的操作日志
            recent_logs = operation_log_service.get_user_logs(
                user_id=user.id,
                per_page=5
            )
            # 记录成功日志
            current_app.logger.info(
                f'成功获取用户 {user.username} 的编辑页面数据',
                extra={
                    'user_id': user.id,
                    'username': user.username,
                    'stats': stats,
                    'logs_count': recent_logs.total if hasattr(recent_logs, 'total') else 0,
                    'action': 'get_user_edit_page_data',
                    'status': 'success'
                }
            )
            
            # 记录操作日志
            operation_log_service.log_operation(
                user=current_user,
                action='访问用户编辑页面',
                details=f'成功访问用户 {user.username} 的编辑页面，文章数: {stats["posts_count"]}，评论数: {stats["comments_count"]}',
                result='success'
            )
            
            # 创建表单对象并预填充用户数据
            form = RegisterForm(obj=user)
            return render_template('admin/user/edit.html',
                user=user,
                roles=roles,
                stats=stats,
                recent_logs=recent_logs.items if hasattr(recent_logs, 'items') else [],
                form=form,
                is_edit=True,
                is_admin_user=user.is_admin_user  # 传递是否为超级管理员用户标识
            )
        
        elif request.method == 'POST':
            try:
                # 创建表单对象以便在验证失败时重新渲染
                form = RegisterForm(obj=user)
                
                # 获取表单数据
                username = request.form.get('username')
                email = request.form.get('email')
                nickname = request.form.get('nickname', '')
                password = request.form.get('password', '')
                is_active = request.form.get('is_active') == 'on'
                role_ids = request.form.getlist('roles')
                
                # 记录表单数据（调试）
                current_app.logger.debug(f'表单数据: username={username}, email={email}, nickname={nickname}, password={password or "空"}, is_active={is_active}, role_ids={role_ids}')
                
                # 检查提交的角色列表
                current_app.logger.debug(f'提交的角色ID列表: {role_ids}')
                for role_id in role_ids:
                    current_app.logger.debug(f'检查角色ID: {role_id}')
                    role = Role.query.get(role_id)
                    if role:
                        current_app.logger.debug(f'找到角色: {role.name} (ID: {role.id})')
                    else:
                        current_app.logger.warning(f'找不到角色ID: {role_id}')
                
                # 记录原始用户信息以便记录日志
                old_user_info = user.to_dict()
                
                # 特殊处理超级管理员用户
                if user.is_admin_user:
                    # 超级管理员用户名不能修改
                    username = user.username
                    
                    # 超级管理员必须具有超级管理员角色
                    super_admin_role = Role.query.filter_by(name='super_admin').first()
                    if super_admin_role:
                        role_ids = [str(super_admin_role.id)]
                        current_app.logger.debug(f'自动添加超级管理员角色ID: {role_ids}')
                    
                    # 超级管理员用户必须处于激活状态
                    is_active = True
                
                # 记录编辑尝试
                current_app.logger.info(
                    f'用户 {current_user.username} 尝试编辑用户 {user.username}. '
                    f'New values - Email: {email}, Roles: {role_ids}, Active: {is_active}'
                )
                
                # 收集验证错误
                validation_errors = []
                
                # 验证用户名
                if not username:
                    validation_errors.append('用户名不能为空')
                elif len(username) < 3:
                    validation_errors.append('用户名长度不能少于3个字符')
                elif not re.match(r'^[a-zA-Z0-9_-]+$', username):
                    validation_errors.append('用户名只能包含字母、数字、下划线和短横线')
                
                # 验证邮箱
                if not email:
                    validation_errors.append('邮箱地址不能为空')
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                    validation_errors.append('请输入有效的邮箱地址')
                
                # 验证角色
                if not role_ids and not user.is_super_admin:
                    validation_errors.append('请至少选择一个角色')
                
                # 如果有验证错误
                if validation_errors:
                    error_msg = '\n'.join(validation_errors)
                    current_app.logger.warning(
                        f'用户 {current_user.username} 编辑用户 {user.username} 失败: '
                        f'表单验证错误 - {error_msg}'
                    )
                    
                    # 使用flash消息并重新渲染页面，而不是返回JSON
                    for error in validation_errors:
                        flash(error, 'danger')
                        
                    # 获取用户最新的统计信息和日志
                    try:
                        stats = {
                            'posts_count': len(user.posts) if hasattr(user, 'posts') else 0,
                            'comments_count': user.comments.count() if hasattr(user, 'comments') else 0,
                            'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                            'is_active': user.is_active,
                            'last_login': getattr(user, 'last_login', None),
                            'created_at': user.created_at,
                            'updated_at': user.updated_at
                        }
                    except Exception as e:
                        current_app.logger.warning(f'获取用户统计信息失败: {str(e)}')
                        stats = {
                            'posts_count': 0,
                            'comments_count': 0,
                            'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                            'is_active': user.is_active,
                            'last_login': getattr(user, 'last_login', None),
                            'created_at': user.created_at,
                            'updated_at': user.updated_at
                        }
                    
                    recent_logs = operation_log_service.get_user_logs(
                        user_id=user.id,
                        per_page=5
                    )
                    
                    return render_template('admin/user/edit.html',
                        user=user,
                        roles=roles,
                        stats=stats,
                        recent_logs=recent_logs.items if hasattr(recent_logs, 'items') else [],
                        form=form,
                        is_edit=True,
                        is_admin_user=user.is_admin_user
                    )
                
                # 更新用户信息
                current_app.logger.debug(f'调用update_user: user_id={user_id}, username={username}, email={email}, nickname={nickname}, password={"非空" if password else "空"}, is_active={is_active}, role_ids={role_ids}')
                result = user_service.update_user(
                    user_id=user_id,
                    username=username,
                    email=email,
                    nickname=nickname,
                    password=password,
                    is_active=is_active,
                    role_ids=role_ids
                )
                
                current_app.logger.debug(f'update_user结果: {result}')
                
                if result['status']:
                    # 获取更新后的用户信息
                    new_user_info = user.to_dict()
                    
                    # 记录操作日志
                    operation_log_service.log_operation(
                        user=current_user,
                        action='编辑用户',
                        details=f'编辑用户 {username}',
                        result='success'
                    )
                    
                    current_app.logger.info(f'用户 {current_user.username} 成功编辑用户 {username}')
                    # 不再返回JSON响应，而是重定向到用户列表页面
                    flash('用户信息已成功更新', 'success')
                    return redirect(url_for('admin_dashboard.user.index'))
                else:
                    error_msg = f'编辑用户失败: {result["message"]}'
                    current_app.logger.warning(error_msg)
                    operation_log_service.log_operation(
                        user=current_user,
                        action='编辑用户',
                        details=f'编辑用户 {username if "username" in locals() else user.username} 过程发生错误: {error_msg}',
                        result='error'
                    )
                    
                    # 显示错误消息并保持在当前页面
                    flash(result['message'], 'danger')
                    return redirect(url_for('admin_dashboard.user.edit', user_id=user_id))
                    
            except Exception as e:
                error_msg = f'更新用户信息失败: {str(e)}'
                current_app.logger.error(error_msg)
                current_app.logger.exception(e)
                
                operation_log_service.log_operation(
                    user=current_user,
                    action='编辑用户',
                    details=f'编辑用户 {username if "username" in locals() else user.username} 过程发生错误: {error_msg}',
                    result='error'
                )
                
                # 返回错误消息并保持在当前页面
                flash('系统错误，请稍后重试', 'danger')
                return redirect(url_for('admin_dashboard.user.edit', user_id=user_id))
    
    except Exception as e:
        error_msg = f'获取用户编辑页面数据出错: {str(e)}'
        extra_data = {
            'error': str(e),
            'traceback': traceback.format_exc(),
            'action': 'get_user_edit_page_data',
            'status': 'error'
        }
        
        # 如果user已经被定义，添加用户信息到日志
        if user is not None:
            extra_data.update({
                'user_id': user.id,
                'username': user.username
            })
        else:
            extra_data.update({
                'user_id': user_id,
                'username': 'unknown'
            })
            
        current_app.logger.error(error_msg, extra=extra_data)
        
        # 记录错误日志
        operation_log_service.log_operation(
            user=current_user,
            action='访问用户编辑页面',
            details=f'获取用户编辑页面数据出错: {str(e)}，用户ID: {user_id}',
            result='error'
        )
        
        return render_template('admin/error.html',
            error='获取用户数据失败',
            error_code=500,
            show_debug_info=current_app.debug,
            error_details={
                'message': str(e),
                'type': type(e).__name__,
                'traceback': traceback.format_exc() if current_app.debug else None
            },
            suggestion='请刷新页面或稍后重试'
        ), 500

@user_bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """删除用户"""
    try:
        # 记录删除尝试
        current_app.logger.info(f'用户 {current_user.username} 尝试删除用户 ID: {user_id}')
        
        # 检查是否有权限删除
        if not has_delete_permission(current_user, user_id):
            error_msg = f'用户 {current_user.username} 尝试删除用户 {user_id} 失败: 权限不足'
            current_app.logger.warning(error_msg)
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=error_msg,
                result='forbidden'
            )
            flash('您没有权限删除此用户', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 获取要删除的用户
        user = User.query.get(user_id)
        if not user:
            error_msg = f'删除用户失败: 用户 {user_id} 不存在'
            current_app.logger.error(error_msg)
            flash('用户不存在', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 检查特殊账号
        if user.username in ['admin', 'superadmin'] or user.is_admin_user:
            error_msg = f'用户 {current_user.username} 尝试删除超级管理员账号 {user.username}'
            current_app.logger.warning(error_msg)
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=error_msg,
                result='forbidden'
            )
            flash('不能删除超级管理员账号', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 记录用户信息以便记录日志
        username = user.username
        user_info = {"username": user.username, "id": user.id}
        
        try:
            # 开始事务
            db.session.begin()
            current_app.logger.debug(f'开始删除用户 {username} (ID: {user_id}) 的相关数据')
            
            # 处理通知
            try:
                from app.models.notification import Notification
                current_app.logger.debug(f'删除用户通知')
                Notification.query.filter_by(user_id=user_id).delete()
            except Exception as e:
                current_app.logger.warning(f'删除用户通知时出错: {str(e)}')
            
            # 处理操作日志
            try:
                from app.models.operation_log import OperationLog
                current_app.logger.debug(f'删除用户操作日志')
                OperationLog.query.filter_by(user_id=user_id).delete()
            except Exception as e:
                current_app.logger.warning(f'删除用户操作日志时出错: {str(e)}')
            
            # 处理评论
            try:
                from app.models.comment import Comment
                current_app.logger.debug(f'删除用户评论')
                Comment.query.filter_by(author_id=user_id).delete()
            except Exception as e:
                current_app.logger.warning(f'删除用户评论时出错: {str(e)}')
            
            # 处理文章
            try:
                from app.models.post import Post
                current_app.logger.debug(f'处理用户文章')
                
                # 获取用户的所有文章
                posts = Post.query.filter_by(author_id=user_id).all()
                
                # 处理每篇文章的标签关联
                for post in posts:
                    try:
                        current_app.logger.debug(f'移除文章 {post.id} 的标签关联')
                        post.tags = []
                    except Exception as e:
                        current_app.logger.warning(f'移除文章 {post.id} 标签关联时出错: {str(e)}')
                
                # 提交标签关联的更改
                db.session.flush()
                
                # 删除所有文章
                current_app.logger.debug(f'删除用户文章')
                Post.query.filter_by(author_id=user_id).delete()
            except Exception as e:
                current_app.logger.warning(f'处理用户文章时出错: {str(e)}')
                raise e
            
            # 删除用户角色关联
            try:
                current_app.logger.debug(f'删除用户角色关联')
                user.roles = []
                db.session.flush()
            except Exception as e:
                current_app.logger.warning(f'删除用户角色关联时出错: {str(e)}')
                raise e
            
            # 直接删除用户对象
            current_app.logger.debug(f'删除用户对象')
            db.session.delete(user)
            
            # 提交事务
            current_app.logger.debug(f'提交事务')
            db.session.commit()
            
            # 记录操作日志
            current_app.logger.debug(f'记录操作日志')
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=f'成功删除用户 {username}',
                result='success'
            )
            
            current_app.logger.info(f'用户 {current_user.username} 成功删除用户 {username}')
            flash('用户删除成功', 'success')
            return redirect(url_for('admin_dashboard.user.index'))
            
        except Exception as e:
            # 回滚事务
            db.session.rollback()
            error_msg = f'删除用户数据过程中发生错误: {str(e)}'
            current_app.logger.error(error_msg)
            current_app.logger.exception(e)
            
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=f'删除用户数据时发生错误: {error_msg}',
                result='error'
            )
            
            flash('删除失败，数据库操作错误', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
    except Exception as e:
        db.session.rollback()
        error_msg = f'删除用户失败: {str(e)}'
        current_app.logger.error(error_msg)
        current_app.logger.exception(e)
        
        operation_log_service.log_operation(
            user=current_user,
            action='删除用户',
            details=f'删除用户时发生错误: {error_msg}',
            result='error'
        )
        
        flash('删除失败，请稍后重试', 'danger')
        return redirect(url_for('admin_dashboard.user.index'))

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改密码"""
    try:
        # 记录修改密码尝试
        current_app.logger.info(f'用户 {current_user.username} 尝试修改密码')
        
        # 获取表单数据
        try:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            # 验证表单数据完整性
            if not all([old_password, new_password, confirm_password]):
                error_msg = '密码修改失败: 表单数据不完整'
                current_app.logger.warning(error_msg)
                operation_log_service.log_operation(
                    user=current_user,
                    action='修改密码',
                    details=error_msg,
                    result='failed'
                )
                
                # 使用flash消息并重定向，而不是返回JSON
                flash('请填写所有必填字段', 'danger')
                return redirect(url_for('auth.profile'))
        except Exception as e:
            error_msg = f'获取表单数据失败: {str(e)}'
            current_app.logger.error(error_msg)
            current_app.logger.exception(e)
            
            operation_log_service.log_operation(
                user=current_user,
                action='修改密码',
                details=f'获取表单数据失败: {error_msg}',
                result='error'
            )
            
            # 使用flash消息并重定向，而不是返回JSON
            flash('系统错误，请稍后重试', 'danger')
            return redirect(url_for('auth.profile'))
        
        # 验证新密码
        if new_password != confirm_password:
            error_msg = '密码修改失败: 两次输入的新密码不一致'
            current_app.logger.warning(error_msg)
            operation_log_service.log_operation(
                user=current_user,
                action='修改密码',
                details=error_msg,
                result='failed'
            )
            
            # 使用flash消息并重定向，而不是返回JSON
            flash('两次输入的密码不一致', 'danger')
            return redirect(url_for('auth.profile'))
        
        # 验证密码复杂度
        try:
            if len(new_password) < 8:
                error_msg = '密码修改失败: 新密码长度不足8位'
                current_app.logger.warning(error_msg)
                operation_log_service.log_operation(
                    user=current_user,
                    action='修改密码',
                    details=error_msg,
                    result='failed'
                )
                
                # 使用flash消息并重定向，而不是返回JSON
                flash('新密码长度不能少于8位', 'danger')
                return redirect(url_for('auth.profile'))
            
            if not any(c.isupper() for c in new_password) or \
               not any(c.islower() for c in new_password) or \
               not any(c.isdigit() for c in new_password):
                error_msg = '密码修改失败: 新密码必须包含大小写字母和数字'
                current_app.logger.warning(error_msg)
                operation_log_service.log_operation(
                    user=current_user,
                    action='修改密码',
                    details=error_msg,
                    result='failed'
                )
                
                # 使用flash消息并重定向，而不是返回JSON
                flash('新密码必须包含大小写字母和数字', 'danger')
                return redirect(url_for('auth.profile'))
        except Exception as e:
            error_msg = f'验证密码复杂度失败: {str(e)}'
            current_app.logger.error(error_msg)
            current_app.logger.exception(e)
            
            operation_log_service.log_operation(
                user=current_user,
                action='修改密码',
                details=f'验证密码复杂度失败: {error_msg}',
                result='error'
            )
            
            # 使用flash消息并重定向，而不是返回JSON
            flash('系统错误，请稍后重试', 'danger')
            return redirect(url_for('auth.profile'))
        
        # 更新密码
        try:
            user_service.change_password(
                current_user.id,
                old_password,
                new_password
            )
            
            # 记录成功日志
            current_app.logger.info(f'用户 {current_user.username} 成功修改密码')
            operation_log_service.log_operation(
                user=current_user,
                action='修改密码',
                details='密码修改成功',
                result='success'
            )
            
            # 使用flash消息并重定向，而不是返回JSON
            flash('密码修改成功，请重新登录', 'success')
            return redirect(url_for('auth.logout'))
        except Exception as e:
            error_msg = f'更新密码失败: {str(e)}'
            current_app.logger.error(error_msg)
            current_app.logger.exception(e)
            
            operation_log_service.log_operation(
                user=current_user,
                action='修改密码',
                details=f'更新密码失败: {error_msg}',
                result='error'
            )
            
            # 使用flash消息并重定向，而不是返回JSON
            flash('修改密码失败，请稍后重试', 'danger')
            return redirect(url_for('auth.profile'))
            
    except Exception as e:
        error_msg = f'修改密码失败: {str(e)}'
        current_app.logger.error(error_msg)
        current_app.logger.exception(e)
        
        operation_log_service.log_operation(
            user=current_user,
            action='修改密码',
            details=f'密码修改过程发生未知错误: {error_msg}',
            result='error'
        )
        
        # 使用flash消息并重定向，而不是返回JSON
        flash('系统错误，请稍后重试', 'danger')
        return redirect(url_for('auth.profile'))

@user_bp.route('/<int:user_id>/direct_delete', methods=['POST'])
@login_required
@admin_required
def direct_delete(user_id):
    """直接使用SQL删除用户（用于处理ORM可能导致的问题）"""
    try:
        # 记录删除尝试
        current_app.logger.info(f'用户 {current_user.username} 尝试直接删除用户 ID: {user_id}')
        
        # 检查是否有权限删除
        if not has_delete_permission(current_user, user_id):
            error_msg = f'用户 {current_user.username} 尝试删除用户 {user_id} 失败: 权限不足'
            current_app.logger.warning(error_msg)
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=error_msg,
                result='forbidden'
            )
            flash('您没有权限删除此用户', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 获取要删除的用户
        user = User.query.get(user_id)
        if not user:
            error_msg = f'删除用户失败: 用户 {user_id} 不存在'
            current_app.logger.error(error_msg)
            flash('用户不存在', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 检查特殊账号
        if user.username in ['admin', 'superadmin'] or user.is_admin_user:
            error_msg = f'用户 {current_user.username} 尝试删除超级管理员账号 {user.username}'
            current_app.logger.warning(error_msg)
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=error_msg,
                result='forbidden'
            )
            flash('不能删除超级管理员账号', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 记录用户信息以便记录日志
        username = user.username
        user_info = {"username": user.username, "id": user.id}
        
        # 检查数据库连接
        if not db.engine.url.database:
            error_msg = f'数据库连接配置错误'
            current_app.logger.error(error_msg)
            flash('系统错误: 数据库连接配置错误', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        
        # 记录使用的数据库路径
        db_path = db.engine.url.database
        current_app.logger.debug(f'使用的数据库路径: {db_path}')
        
        # 外键状态标志，用于跟踪是否需要重新启用外键约束
        fk_disabled = False
        
        try:
            # 检查外键约束当前状态
            fk_status = db.session.execute(db.text("PRAGMA foreign_keys")).scalar()
            current_app.logger.debug(f'当前外键约束状态: {fk_status}')
            
            # 临时关闭外键约束检查
            db.session.execute(db.text("PRAGMA foreign_keys = OFF"))
            fk_disabled = True
            current_app.logger.debug('已临时关闭外键约束')
            
            # 使用最简单的方式删除
            # 1. 先删除用户角色关联
            current_app.logger.debug(f'删除用户角色关联')
            result = db.session.execute(db.text(f"DELETE FROM user_roles WHERE user_id = {user_id}"))
            if result.rowcount == 0:
                current_app.logger.debug(f'用户 {user_id} 没有关联角色')
            else:
                current_app.logger.debug(f'成功删除 {result.rowcount} 条用户角色关联')
                
            # 2. 删除用户本身
            current_app.logger.debug(f'删除用户记录')
            result = db.session.execute(db.text(f"DELETE FROM users WHERE id = {user_id}"))
            if result.rowcount == 0:
                raise Exception(f'用户 {user_id} 不存在或删除失败')
            current_app.logger.debug(f'成功删除用户 {username}')
            
            # 提交事务
            db.session.commit()
            current_app.logger.info(f'事务已提交，用户 {username} 已成功删除')
            
            # 记录操作日志
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=f'成功直接删除用户 {username}',
                result='success'
            )
            
            flash('用户删除成功', 'success')
            return redirect(url_for('admin_dashboard.user.index'))
            
        except Exception as e:
            # 回滚事务
            try:
                db.session.rollback()
                current_app.logger.debug('事务已回滚')
            except Exception as rollback_err:
                current_app.logger.error(f'回滚事务失败: {str(rollback_err)}')
            
            error_msg = f'直接删除用户数据过程中发生错误: {str(e)}'
            current_app.logger.error(error_msg)
            current_app.logger.exception(e)
            
            operation_log_service.log_operation(
                user=current_user,
                action='删除用户',
                details=f'直接删除用户数据时发生错误: {error_msg}',
                result='error'
            )
            
            flash(f'删除失败，数据库操作错误: {str(e)}', 'danger')
            return redirect(url_for('admin_dashboard.user.index'))
        finally:
            # 确保在任何情况下都重新启用外键约束
            if fk_disabled:
                try:
                    db.session.execute(db.text("PRAGMA foreign_keys = ON"))
                    current_app.logger.debug('已重新启用外键约束')
                except Exception as fk_err:
                    current_app.logger.error(f'重新启用外键约束失败: {str(fk_err)}')
        
    except Exception as e:
        try:
            db.session.rollback()
            current_app.logger.debug('外部事务已回滚')
        except:
            pass
            
        # 确保外键约束被重新启用
        try:
            db.session.execute(db.text("PRAGMA foreign_keys = ON"))
            current_app.logger.debug('已重新启用外键约束（外部异常处理）')
        except Exception as fk_err:
            current_app.logger.error(f'在外部异常处理中重新启用外键约束失败: {str(fk_err)}')
            
        error_msg = f'删除用户失败: {str(e)}'
        current_app.logger.error(error_msg)
        current_app.logger.exception(e)
        
        operation_log_service.log_operation(
            user=current_user,
            action='删除用户',
            details=f'删除用户时发生错误: {error_msg}',
            result='error'
        )
        
        flash(f'删除失败: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard.user.index'))