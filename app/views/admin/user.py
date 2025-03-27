"""
文件名：user.py
描述：用户管理视图
作者：denny
创建日期：2024-03-26
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app.forms.auth import RegisterForm
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from app.decorators import admin_required

# 创建蓝图
bp = Blueprint('user', __name__)

@bp.route('/')
@login_required
@admin_required
def index():
    """用户列表页面"""
    users = User.query.all()
    current_app.logger.info(f"访问用户列表页面: {len(users)} 个用户")
    return render_template('admin/user/list.html', users=users)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    """创建用户页面"""
    # 日志记录 - 调试访问
    current_app.logger.info(f"===== 访问用户创建页面 =====")
    current_app.logger.info(f"请求方法: {request.method}")
    current_app.logger.info(f"用户: {current_user.username}")
    current_app.logger.info(f"IP地址: {request.remote_addr}")

    # 获取所有角色，并过滤掉super_admin, admin和user角色
    all_roles = Role.query.all()
    roles = [role for role in all_roles if role.name not in ['super_admin', 'admin', 'user']]
    current_app.logger.info(f"可用角色数量: {len(roles)}")
    
    if request.method == 'POST':
        # 记录原始POST数据
        current_app.logger.info(f"表单提交方法: {request.method}")
        current_app.logger.info(f"表单提交路径: {request.path}")
        current_app.logger.info(f"Content-Type: {request.headers.get('Content-Type')}")
        current_app.logger.info(f"表单键值: {list(request.form.keys())}")
        
        # 敏感数据不记录实际值
        safe_form_keys = [k for k in request.form.keys() if k not in ['password', 'password2']]
        safe_form_data = {k: request.form.get(k) for k in safe_form_keys}
        current_app.logger.info(f"表单数据(安全版本): {safe_form_data}")
        
        # 直接从请求表单获取数据，而不是通过WTForms
        username = request.form.get('username')
        email = request.form.get('email')
        nickname = request.form.get('nickname', '')
        password = request.form.get('password')
        password2 = request.form.get('password2')
        is_active = request.form.get('is_active') == 'on'
        selected_roles = request.form.getlist('roles')
        
        # 自定义验证
        validation_passed = True
        error_messages = []
        
        # 验证用户名
        if not username:
            validation_passed = False
            error_messages.append('用户名不能为空')
        elif username.lower() == 'admin':
            validation_passed = False
            error_messages.append('不能使用保留的用户名')
        elif User.query.filter_by(username=username).first():
            validation_passed = False
            error_messages.append('该用户名已被使用')
        
        # 验证邮箱
        if not email:
            validation_passed = False
            error_messages.append('邮箱不能为空')
        elif User.query.filter_by(email=email).first():
            validation_passed = False
            error_messages.append('该邮箱已被注册')
        
        # 验证密码
        if not password:
            validation_passed = False
            error_messages.append('密码不能为空')
        elif password != password2:
            validation_passed = False
            error_messages.append('两次输入的密码不一致')
        
        # 记录验证结果
        current_app.logger.info(f"验证结果: {validation_passed}")
        if not validation_passed:
            current_app.logger.info(f"验证错误: {error_messages}")
        
        if validation_passed:
            try:
                # 创建用户对象
                user = User(
                    username=username,
                    email=email,
                    nickname=nickname,
                    is_active=is_active
                )
                
                # 设置密码
                user.set_password(password)
                
                current_app.logger.info(f"用户对象创建: {user.username}, {user.email}")
                
                # 设置用户角色
                current_app.logger.info(f"selected_roles: {selected_roles}")
                
                # 无论如何都会分配角色
                roles_added = False
                
                # 1. 尝试使用用户选择的角色
                if selected_roles:
                    for role_id in selected_roles:
                        try:
                            role = Role.query.get(role_id)
                            current_app.logger.info(f"找到角色: ID={role_id}, 名称={role.name if role else 'None'}")
                            if role and role.name not in ['super_admin', 'admin', 'user']:
                                user.roles.append(role)
                                current_app.logger.info(f"成功添加角色: {role.name}")
                                roles_added = True
                        except Exception as e:
                            current_app.logger.error(f"添加角色时出错: {str(e)}")
                
                # 2. 如果没有添加角色，无论如何都分配一个
                if not roles_added:
                    try:
                        # 尝试查找可用角色列表
                        available_roles = Role.query.filter(~Role.name.in_(['super_admin', 'admin', 'user'])).all()
                        current_app.logger.info(f"可用角色列表: {[r.name for r in available_roles]}")
                        
                        if available_roles:
                            # 使用第一个可用角色
                            first_role = available_roles[0]
                            user.roles.append(first_role)
                            current_app.logger.info(f"使用第一个可用角色: {first_role.name}")
                            roles_added = True
                        else:
                            # 如果没有可用角色，创建一个新的编辑者角色
                            current_app.logger.warning("找不到可用角色，创建新的编辑者角色")
                            new_role = Role(name='editor_new', description='新编辑者', permissions=7)
                            db.session.add(new_role)
                            db.session.flush()  # 获取ID但不提交
                            user.roles.append(new_role)
                            current_app.logger.info(f"创建并添加新角色: {new_role.name}")
                            roles_added = True
                    except Exception as e:
                        current_app.logger.error(f"设置默认角色时出错: {str(e)}")
                        flash(f'创建用户失败: 无法分配角色 - {str(e)}', 'error')
                        return render_template('admin/user/create.html', form=RegisterForm(), roles=roles)
                
                # 保存用户到数据库
                current_app.logger.info("正在保存用户到数据库...")
                db.session.add(user)
                
                try:
                    db.session.commit()
                    user_id = user.id
                    current_app.logger.info(f"数据库提交成功! 用户ID: {user_id}")
                    
                    # 数据库验证 - 确认用户已保存
                    saved_user = User.query.get(user_id)
                    if saved_user:
                        current_app.logger.info(f"用户创建验证成功: ID={saved_user.id}, 用户名={saved_user.username}, 角色={[r.name for r in saved_user.roles]}")
                        
                        # 提示成功并重定向
                        flash('用户创建成功', 'success')
                        # 使用url_for替代硬编码URL
                        redirect_url = url_for('admin_dashboard.user.index')
                        current_app.logger.info(f"重定向到: {redirect_url}")
                        return redirect(redirect_url)
                    else:
                        current_app.logger.error(f"无法找到刚创建的用户ID={user_id}")
                        flash(f'创建用户成功但无法验证，请刷新用户列表', 'warning')
                        return redirect(url_for('admin_dashboard.user.index'))
                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"提交到数据库时出错: {str(e)}", exc_info=True)
                    flash(f'创建用户失败: 数据库错误 - {str(e)}', 'error')
                    return render_template('admin/user/create.html', form=RegisterForm(), roles=roles)
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"创建用户失败: {str(e)}", exc_info=True)
                flash(f'创建用户失败: {str(e)}', 'error')
                return render_template('admin/user/create.html', form=RegisterForm(), roles=roles)
        else:
            # 显示验证错误
            for error in error_messages:
                flash(error, 'error')
            return render_template('admin/user/create.html', form=RegisterForm(), roles=roles)
    else:
        # GET请求时创建一个空的表单实例
        form = RegisterForm()
    
    return render_template('admin/user/create.html', form=form, roles=roles)

@bp.route('/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(user_id):
    """编辑用户页面"""
    user = User.query.get_or_404(user_id)
    form = RegisterForm(obj=user)
    
    # 判断是否是超级管理员用户
    is_admin_user = user.username == 'admin'
    
    # 获取所有角色
    all_roles = Role.query.all()
    
    # 对于超级管理员用户，只显示super_admin角色
    # 对于普通用户，过滤掉super_admin、admin和user角色
    if is_admin_user:
        roles = [role for role in all_roles if role.name == 'super_admin']
    else:
        roles = [role for role in all_roles if role.name not in ['super_admin', 'admin', 'user']]
    
    if request.method == 'POST' and form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.nickname = form.nickname.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # 处理角色
        user.roles = []
        
        # 对于超级管理员用户，保持其super_admin角色
        if is_admin_user:
            super_admin_role = Role.query.filter_by(name='super_admin').first()
            if super_admin_role:
                user.roles.append(super_admin_role)
        else:
            # 为普通用户添加选中的角色，但确保不包含super_admin角色
            selected_roles = request.form.getlist('roles')
            if selected_roles:
                for role_id in selected_roles:
                    role = Role.query.get(role_id)
                    if role and role.name not in ['super_admin', 'admin', 'user']:
                        user.roles.append(role)
        
        db.session.commit()
        flash('用户更新成功', 'success')
        return redirect(url_for('admin_dashboard.user.index'))
    
    return render_template('admin/user/edit.html', form=form, user=user, roles=roles, is_admin_user=is_admin_user, is_edit=True)

@bp.route('/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)
    
    # 禁止删除admin用户
    if user.username == 'admin':
        flash('不能删除管理员用户', 'error')
        return redirect(url_for('admin_dashboard.user.index'))
    
    db.session.delete(user)
    db.session.commit()
    flash('用户删除成功', 'success')
    return redirect(url_for('admin_dashboard.user.index'))

@bp.route('/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(user_id):
    """切换用户状态"""
    user = User.query.get_or_404(user_id)
    
    # 禁止禁用admin用户
    if user.username == 'admin' and user.is_active:
        flash('不能禁用管理员用户', 'error')
        return redirect(url_for('admin_dashboard.user.index'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = '启用' if user.is_active else '禁用'
    flash(f'用户已{status}', 'success')
    return redirect(url_for('admin_dashboard.user.index'))
