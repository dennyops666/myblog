"""
文件名：__init__.py
描述：认证蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService, OperationLogService
from app.models import User, Permission
from app.forms.auth import LoginForm
from urllib.parse import urlparse
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.exceptions import BadRequest
import traceback

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理后台登录视图"""
    form = LoginForm()

    # 如果是GET请求，返回登录页面
    if request.method == 'GET':
        # 如果已经登录，重定向到管理后台
        if current_user.is_authenticated:
            return redirect(url_for('admin.index'))
        # 生成新的CSRF令牌
        csrf_token = generate_csrf()
        response = make_response(render_template('auth/login.html', form=form))
        response.set_cookie(
            'csrf_token',
            csrf_token,
            max_age=3600,
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        return response

    # 处理POST请求
    try:
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # 生成新的CSRF令牌
        csrf_token = generate_csrf()

        if not form.validate():
            if is_ajax:
                errors = {field: errors[0] for field, errors in form.errors.items()}
                response = jsonify({
                    'success': False,
                    'message': '表单验证失败',
                    'errors': errors,
                    'csrf_token': csrf_token
                })
                response.status_code = 400
            else:
                response = make_response(render_template('auth/login.html', form=form))
            
            response.set_cookie(
                'csrf_token',
                csrf_token,
                max_age=3600,
                secure=False,
                httponly=False,
                samesite='Lax'
            )
            return response

        # 如果已经登录，返回相应响应
        if current_user.is_authenticated:
            if is_ajax:
                response = jsonify({
                    'success': True,
                    'message': '已经登录',
                    'redirect_url': url_for('admin.index', _external=True),
                    'csrf_token': csrf_token
                })
            else:
                response = redirect(url_for('admin.index'))
            
            response.set_cookie(
                'csrf_token',
                csrf_token,
                max_age=3600,
                secure=False,
                httponly=False,
                samesite='Lax'
            )
            return response

        user = user_service.get_user_by_username(form.username.data)
        if not user or not user.verify_password(form.password.data):
            if is_ajax:
                response = jsonify({
                    'success': False,
                    'message': '用户名或密码错误',
                    'csrf_token': csrf_token
                })
                response.status_code = 401
            else:
                flash('用户名或密码错误', 'danger')
                response = make_response(render_template('auth/login.html', form=form))
            
            response.set_cookie(
                'csrf_token',
                csrf_token,
                max_age=3600,
                secure=False,
                httponly=False,
                samesite='Lax'
            )
            return response

        # 检查管理员权限
        is_admin = False
        for role in user.roles:
            if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                is_admin = True
                break

        if not is_admin:
            if is_ajax:
                response = jsonify({
                    'success': False,
                    'message': '您不是管理员，请从博客首页登录',
                    'redirect_url': url_for('blog.login', _external=True),
                    'csrf_token': csrf_token
                })
                response.status_code = 403
            else:
                flash('您不是管理员，请从博客首页登录', 'danger')
                response = redirect(url_for('blog.login'))
            
            response.set_cookie(
                'csrf_token',
                csrf_token,
                max_age=3600,
                secure=False,
                httponly=False,
                samesite='Lax'
            )
            return response

        # 登录成功处理
        session.clear()
        session.permanent = True
        login_user(user, remember=form.remember_me.data)

        # 记录操作日志
        OperationLogService.log_operation(
            user=user,
            action='admin_login',
            details=f'管理员 {user.username} 登录后台'
        )

        # 准备响应
        if is_ajax:
            response = jsonify({
                'success': True,
                'message': '登录成功',
                'redirect_url': url_for('admin.index', _external=True),
                'csrf_token': csrf_token
            })
        else:
            flash('登录成功', 'success')
            response = redirect(url_for('admin.index'))

        # 设置cookie
        response.set_cookie(
            'csrf_token',
            csrf_token,
            max_age=3600,
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        response.set_cookie(
            'session_active',
            '1',
            max_age=31536000,
            secure=False,
            httponly=True,
            samesite='Lax'
        )

        return response

    except Exception as e:
        current_app.logger.error(f'登录失败: {str(e)}\n{traceback.format_exc()}')
        if is_ajax:
            response = jsonify({
                'success': False,
                'message': '服务器内部错误',
                'csrf_token': csrf_token
            })
            response.status_code = 500
        else:
            flash('服务器内部错误', 'danger')
            response = make_response(render_template('auth/login.html', form=form))
            response.status_code = 500
        
        response.set_cookie(
            'csrf_token',
            csrf_token,
            max_age=3600,
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        return response

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """登出"""
    try:
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 如果用户未登录，直接返回到登录页
        if not current_user.is_authenticated:
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': '未登录状态',
                    'redirect_url': url_for('auth.login', _external=True)
                })
            return redirect(url_for('auth.login'))
        
        username = current_user.username
        
        # 清除会话和cookie
        logout_user()
        session.clear()
        
        # 生成新的CSRF令牌
        csrf_token = generate_csrf()
        
        # 创建响应对象
        if is_ajax:
            response = jsonify({
                'success': True,
                'message': '已安全退出',
                'redirect_url': url_for('auth.login', _external=True)
            })
        else:
            flash('已安全退出', 'success')
            response = redirect(url_for('auth.login'))
        
        # 删除所有相关的cookie
        response.set_cookie('session_active', '', expires=0)
        response.set_cookie('remember_token', '', expires=0)
        response.set_cookie('session', '', expires=0)
        
        # 设置新的CSRF令牌
        response.set_cookie(
            'csrf_token',
            csrf_token,
            max_age=3600,
            secure=False,
            httponly=False,
            samesite='Lax'
        )
        
        # 记录日志
        current_app.logger.info(f'用户 {username} 已登出')
        
        return response
        
    except Exception as e:
        current_app.logger.error(f'登出过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '服务器内部错误',
                'csrf_token': generate_csrf()
            }), 500
        flash('服务器内部错误', 'error')
        return render_template('errors/500.html'), 500

@auth_bp.route('/refresh-csrf', methods=['GET'])
def refresh_csrf():
    """刷新CSRF令牌"""
    try:
        csrf_token = generate_csrf()
        response = jsonify({
            'success': True,
            'csrf_token': csrf_token
        })
        response.set_cookie(
            'csrf_token',
            csrf_token,
            max_age=3600,  # 1小时
            secure=False,  # 开发环境不要求HTTPS
            httponly=False,  # 允许JavaScript访问
            samesite='Lax'  # 允许跨站请求
        )
        return response
    except Exception as e:
        current_app.logger.error(f'刷新CSRF令牌失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': '刷新CSRF令牌失败'
        }), 500