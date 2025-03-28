"""
文件名：auth.py
描述：认证视图
作者：denny
"""

from flask import (
    Blueprint, render_template, request, url_for, redirect,
    flash, session, current_app, abort, jsonify, make_response
)
from flask_login import (
    login_user, logout_user, login_required,
    current_user
)
from app.forms.auth import LoginForm, RegisterForm, PasswordResetRequestForm, PasswordResetForm, PasswordChangeForm
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from datetime import datetime, timedelta, UTC
from werkzeug.security import check_password_hash
from sqlalchemy import text
from app.utils.security import verify_token
from urllib.parse import urlparse
from app.models.permission import Permission

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录

    Returns:
        response: 响应对象
    """
    if current_user.is_authenticated:
        current_app.logger.info(f"用户已登录: {current_user.username}")
        # 检查用户是否有管理员权限
        is_admin = False
        for role in current_user.roles:
            if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                is_admin = True
                break
        
        # 根据用户权限重定向到不同的页面
        if is_admin:
            return redirect(url_for('admin_dashboard.index'))
        else:
            return redirect(url_for('blog.index'))
    
    form = LoginForm()
    
    # 检查是否是从管理后台退出的
    from_admin = session.get('logout_from_admin', False)
    if from_admin:
        session.pop('logout_from_admin', None)  # 使用后清除
    
    if request.method == 'POST':
        # 检查是否是JSON请求
        is_json_request = request.is_json or request.headers.get('Accept') == 'application/json'
        current_app.logger.info(f"登录请求: is_json_request={is_json_request}")
        
        if is_json_request:
            try:
                data = request.get_json()
                current_app.logger.debug(f"登录请求数据: {data}")
                username = data.get('username', '')
                password = data.get('password', '')
                remember_me = data.get('remember_me', False)
                
                current_app.logger.info(f"JSON登录请求: username={username}, remember_me={remember_me}")
                
                # 验证用户名和密码
                if not username or not password:
                    current_app.logger.info("用户名或密码为空")
                    return jsonify({
                        'status': 'error',
                        'message': '用户名和密码不能为空',
                        'next_url': url_for('auth.login', _external=False)
                    }), 200
                
                # 查询用户
                try:
                    user = User.query.filter_by(username=username).first()
                    current_app.logger.info(f"查询用户结果: {user is not None}")
                    
                    # 检查用户是否存在
                    if user is None:
                        current_app.logger.info(f"用户不存在: {username}")
                        return jsonify({
                            'status': 'error',
                            'message': '用户名或密码错误',
                            'next_url': url_for('auth.login', _external=False)
                        }), 200
                    
                    # 检查用户是否被禁用
                    if not user.is_active:
                        current_app.logger.info(f"用户已被禁用: {username}")
                        current_app.logger.info(f"用户状态: is_active={user.is_active}")
                        current_app.logger.info("返回状态: error, 消息: 账户已被禁用")
                        return jsonify({
                            'status': 'error',
                            'message': '账户已被禁用',
                            'next_url': url_for('auth.login', _external=False)
                        }), 200
                    
                    # 检查密码是否正确
                    try:
                        current_app.logger.info(f"开始验证密码: 用户名={username}, 密码长度={len(password)}")
                        
                        password_correct = user.verify_password(password)
                        current_app.logger.info(f"密码验证结果: {password_correct}")
                        
                        if not password_correct:
                            current_app.logger.info(f"密码错误: 用户名={username}")
                            current_app.logger.info("返回状态: error, 消息: 用户名或密码错误")
                            return jsonify({
                                'status': 'error',
                                'message': '用户名或密码错误',
                                'next_url': url_for('auth.login', _external=False)
                            }), 200
                        
                        # 登录成功
                        current_app.logger.info(f"登录成功: 用户名={username}")
                        login_result = login_user(user, remember=remember_me)
                        current_app.logger.info(f"login_user结果: {login_result}")
                        
                        if login_result:
                            current_app.logger.info(f"用户已登录: {username}, user_id={user.id}")
                            
                            # 检查用户是否有管理员权限
                            is_admin = False
                            for role in user.roles:
                                if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                                    is_admin = True
                                    break
                            
                            # 获取next参数
                            next_page = request.args.get('next')
                            
                            # 如果没有next参数或next参数不是相对URL，则根据用户权限和来源决定重定向到哪个页面
                            if not next_page or urlparse(next_page).netloc != '':
                                # 检查是否是从管理后台退出的
                                from_admin = session.get('logout_from_admin', False)
                                
                                if from_admin and is_admin:
                                    next_page = url_for('admin_dashboard.index')
                                elif is_admin:
                                    next_page = url_for('admin_dashboard.index')
                                else:
                                    next_page = url_for('blog.index')
                            
                            # 对于JSON请求，返回JSON响应
                            if is_json_request:
                                return jsonify({
                                    'status': 'success',
                                    'message': '登录成功',
                                    'next_url': next_page
                                }), 200
                            else:
                                # 对于表单提交，返回重定向
                                return redirect(next_page)
                        else:
                            current_app.logger.error(f"login_user失败: {username}")
                            return jsonify({
                                'status': 'error',
                                'message': '登录失败，请稍后重试',
                                'next_url': url_for('auth.login', _external=False)
                            }), 200
                    except Exception as e:
                        current_app.logger.error(f"密码验证异常: {str(e)}", exc_info=True)
                        return jsonify({
                            'status': 'error',
                            'message': '登录过程中发生错误',
                            'next_url': url_for('auth.login', _external=False)
                        }), 200
                except Exception as e:
                    current_app.logger.error(f"查询用户异常: {str(e)}", exc_info=True)
                    return jsonify({
                        'status': 'error',
                        'message': '登录过程中发生错误',
                        'next_url': url_for('auth.login', _external=False)
                    }), 200
            except Exception as e:
                current_app.logger.error(f"JSON解析异常: {str(e)}", exc_info=True)
                return jsonify({
                    'status': 'error',
                    'message': '登录请求格式错误',
                    'next_url': url_for('auth.login', _external=False)
                }), 200
        else:
            # 表单提交
            if form.validate_on_submit():
                username = form.username.data
                password = form.password.data
                remember_me = form.remember_me.data
                
                current_app.logger.info(f"表单登录请求: username={username}, remember_me={remember_me}")

                # 查询用户
                try:
                    user = User.query.filter_by(username=username).first()
                    current_app.logger.info(f"查询用户结果: {user is not None}")
                    
                    # 检查用户是否存在
                    if user is None:
                        current_app.logger.info(f"用户不存在: {username}")
                        flash('用户名或密码错误', 'danger')
                        return render_template('auth/login.html', form=form, title='登录')
                    
                    # 检查用户是否被禁用
                    if not user.is_active:
                        current_app.logger.info(f"用户已被禁用: {username}")
                        flash('账户已被禁用', 'danger')
                        return render_template('auth/login.html', form=form, title='登录')
                    
                    # 检查密码是否正确
                    try:
                        current_app.logger.info(f"开始验证密码: 用户名={username}")
                        password_correct = user.verify_password(password)
                        current_app.logger.info(f"密码验证结果: {password_correct}")
                        
                        if not password_correct:
                            current_app.logger.info(f"密码错误: 用户名={username}")
                            flash('用户名或密码错误', 'danger')
                            return render_template('auth/login.html', form=form, title='登录')
                        
                        # 登录成功
                        current_app.logger.info(f"登录成功: 用户名={username}")
                        login_result = login_user(user, remember=remember_me)
                        current_app.logger.info(f"login_user结果: {login_result}")
                        
                        if login_result:
                            current_app.logger.info(f"用户已登录: {username}, user_id={user.id}")
                            
                            # 检查用户是否有管理员权限
                            is_admin = False
                            for role in user.roles:
                                if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                                    is_admin = True
                                    break
                            
                            # 获取next参数
                            next_page = request.args.get('next')
                            
                            # 如果没有next参数或next参数不是相对URL，则根据用户权限和来源决定重定向到哪个页面
                            if not next_page or urlparse(next_page).netloc != '':
                                # 检查是否是从管理后台退出的
                                from_admin = session.get('logout_from_admin', False)
                                
                                if from_admin and is_admin:
                                    next_page = url_for('admin_dashboard.index')
                                elif is_admin:
                                    next_page = url_for('admin_dashboard.index')
                                else:
                                    next_page = url_for('blog.index')
                            
                            # 对于表单提交，返回重定向
                            return redirect(next_page)
                        else:
                            current_app.logger.error(f"login_user失败: {username}")
                            return jsonify({
                                'status': 'error',
                                'message': '登录失败，请稍后重试',
                                'next_url': url_for('auth.login', _external=False)
                            }), 200
                    except Exception as e:
                        current_app.logger.error(f"密码验证异常: {str(e)}", exc_info=True)
                        return jsonify({
                            'status': 'error',
                            'message': '登录过程中发生错误',
                            'next_url': url_for('auth.login', _external=False)
                        }), 200
                except Exception as e:
                    current_app.logger.error(f"查询用户异常: {str(e)}", exc_info=True)
                    return jsonify({
                        'status': 'error',
                        'message': '登录过程中发生错误',
                        'next_url': url_for('auth.login', _external=False)
                    }), 200 