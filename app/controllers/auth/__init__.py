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
import traceback

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理后台登录视图"""
    try:
        # 获取next参数
        next_url = request.args.get('next')
        
        # 如果已经登录，重定向到管理后台
        if current_user.is_authenticated:
            return redirect(next_url or url_for('admin.index'))

        form = LoginForm()
        # 处理POST请求
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me', False)

            if not username or not password:
                flash('用户名和密码不能为空', 'danger')
                return render_template('auth/login.html', form=form)

            user = user_service.get_user_by_username(username)
            if not user or not user.verify_password(password):
                flash('用户名或密码错误', 'danger')
                return render_template('auth/login.html', form=form)

            # 检查管理员权限
            is_admin = False
            admin_permission = Permission.ADMIN.value | Permission.SUPER_ADMIN.value
            for role in user.roles:
                if role.permissions & admin_permission:
                    is_admin = True
                    break

            if not is_admin:
                flash('您不是管理员，请从博客首页登录', 'danger')
                return redirect(url_for('blog.login'))

            # 登录成功处理
            login_user(user, remember=remember_me)
            flash('登录成功', 'success')
            
            # 如果有next参数且是相对路径，则跳转到next
            if next_url:
                # 确保next_url是相对路径，防止重定向攻击
                parsed_next = urlparse(next_url)
                if not parsed_next.netloc:
                    return redirect(next_url)
            
            # 默认跳转到管理后台首页
            return redirect(url_for('admin.index'))

        return render_template('auth/login.html', form=form)
    except Exception as e:
        current_app.logger.error(f'登录过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        flash('服务器内部错误', 'error')
        return render_template('errors/500.html'), 500

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
        
        # 记录日志
        current_app.logger.info(f'用户 {username} 已登出')
        
        return response
        
    except Exception as e:
        current_app.logger.error(f'登出过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': '服务器内部错误'
            }), 500
        flash('服务器内部错误', 'error')
        return render_template('errors/500.html'), 500