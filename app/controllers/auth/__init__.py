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
from app.forms.auth import LoginForm, RegisterForm
from urllib.parse import urlparse
import traceback
from app.extensions import db

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录视图"""
    try:
        # 获取next参数
        next_url = request.args.get('next')
        
        # 如果已经登录，重定向到管理后台首页
        if current_user.is_authenticated:
            if request.is_xhr:
                return jsonify({
                    'success': True,
                    'message': '已经登录',
                    'redirect_url': next_url or url_for('admin.index')
                })
            return redirect(next_url or url_for('admin.index'))

        if request.method == 'GET':
            return render_template('auth/login.html')

        # 处理POST请求
        username = request.form.get('username')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me', '').lower() in ['true', '1', 'on', 'yes']

        # 验证用户名和密码是否为空
        if not username or not password:
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            })

        # 获取用户信息
        result = user_service.get_user_by_username(username)
        if not result['success']:
            current_app.logger.warning(f'登录失败: {result["message"]}')
            return jsonify({
                'success': False,
                'message': result['message']
            })

        user = result['user']
        
        # 验证密码
        if not user.verify_password(password):
            current_app.logger.warning(f'密码验证失败: {username}')
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            })

        # 登录用户
        login_user(user, remember=remember_me)
        
        # 记录登录日志
        current_app.logger.info(f'用户 {username} 登录成功')
        
        # 确定重定向URL
        redirect_url = url_for('admin.index')
        if next_url:
            parsed_next = urlparse(next_url)
            if not parsed_next.netloc:  # 确保是相对URL
                redirect_url = next_url

        # 返回成功响应
        return jsonify({
            'success': True,
            'message': '登录成功',
            'redirect_url': redirect_url
        })

    except Exception as e:
        current_app.logger.error(f'登录过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        return jsonify({
            'success': False,
            'message': '服务器内部错误，请稍后重试'
        }), 500

@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """登出"""
    try:
        # 检查是否是AJAX请求
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # 获取来源页面
        referer = request.referrer
        is_from_admin = referer and '/admin/' in referer if referer else False
        
        # 如果用户未登录
        if not current_user.is_authenticated:
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': '未登录状态',
                    'redirect_url': url_for('blog.index' if not is_from_admin else 'auth.login')
                })
            return redirect(url_for('blog.index' if not is_from_admin else 'auth.login'))
        
        username = current_user.username
        
        # 清除会话和cookie
        logout_user()
        session.clear()
        
        # 创建响应对象
        if is_ajax:
            response = jsonify({
                'success': True,
                'message': '已安全退出',
                'redirect_url': url_for('auth.login' if is_from_admin else 'blog.index')
            })
        else:
            flash('已安全退出', 'success')
            response = redirect(url_for('auth.login' if is_from_admin else 'blog.index'))
        
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

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
        
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            nickname=form.nickname.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('注册成功！请登录。', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)