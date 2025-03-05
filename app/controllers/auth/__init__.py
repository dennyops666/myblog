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
            return redirect(next_url or url_for('admin.index'))

        form = LoginForm()
        # 处理POST请求
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me', False)

            if not username or not password:
                if request.is_json:
                    return jsonify({'success': False, 'message': '用户名和密码不能为空'})
                flash('用户名和密码不能为空', 'danger')
                return render_template('auth/login.html', form=form)

            result = user_service.get_user_by_username(username)
            if not result['success']:
                current_app.logger.warning(f'登录失败: {result["message"]}')
                if request.is_json:
                    return jsonify({'success': False, 'message': result['message']})
                flash(result['message'], 'danger')
                return render_template('auth/login.html', form=form)

            user = result['user']
            if not user.verify_password(password):
                current_app.logger.warning(f'密码验证失败: {username}')
                if request.is_json:
                    return jsonify({'success': False, 'message': '用户名或密码错误'})
                flash('用户名或密码错误', 'danger')
                return render_template('auth/login.html', form=form)

            # 登录成功处理
            login_user(user, remember=remember_me)
            
            # 如果有next参数且是相对路径，则跳转到next
            redirect_url = url_for('admin.index')
            if next_url:
                # 确保next_url是相对路径，防止重定向攻击
                parsed_next = urlparse(next_url)
                if not parsed_next.netloc:
                    redirect_url = next_url
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'redirect_url': redirect_url
                })
                
            flash('登录成功', 'success')
            return redirect(redirect_url)

        return render_template('auth/login.html', form=form)
    except Exception as e:
        current_app.logger.error(f'登录过程中发生错误: {str(e)}\n{traceback.format_exc()}')
        if request.is_json:
            return jsonify({'success': False, 'message': '服务器内部错误，请稍后重试'})
        flash('服务器内部错误，请稍后重试', 'error')
        return render_template('auth/login.html', form=form)

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