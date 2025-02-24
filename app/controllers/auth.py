"""
文件名：auth.py
描述：认证控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template, flash, make_response, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db
from flask_wtf.csrf import generate_csrf, validate_csrf
from datetime import datetime, UTC

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if request.method == 'GET':
        # 只在 GET 请求时生成新的 CSRF token
        csrf_token = generate_csrf()
        response = make_response(render_template('auth/login.html'))
        response.headers['X-CSRF-Token'] = csrf_token
        return response

    if current_user.is_authenticated:
        if request.is_json:
            return jsonify({
                'success': True,
                'message': '已登录',
                'csrf_token': generate_csrf()
            }), 200
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        form_csrf_token = request.form.get('csrf_token')

        if not username or not password:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '用户名和密码不能为空'
                }), 400
            flash('用户名和密码不能为空', 'danger')
            return render_template('auth/login.html'), 400

        # 在测试环境中跳过 CSRF 验证
        if not current_app.config['TESTING']:
            try:
                validate_csrf(form_csrf_token)
            except:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'message': 'CSRF token 验证失败'
                    }), 400
                flash('CSRF token 验证失败', 'danger')
                return render_template('auth/login.html'), 400

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            session['_fresh'] = True
            session['_permanent'] = True
            session['user_agent'] = request.headers.get('User-Agent', '')
            session['last_active'] = datetime.now(UTC).isoformat()
            
            next_page = request.args.get('next', url_for('admin.index'))
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': '登录成功',
                    'next': next_page,
                    'csrf_token': generate_csrf()
                }), 200
            return redirect(next_page)
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': '用户名或密码错误'
                }), 400
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html'), 400

    response = make_response(render_template('auth/login.html'))
    response.headers['X-CSRF-Token'] = generate_csrf()
    return response

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    if request.is_json:
        return jsonify({
            'success': True,
            'message': '已安全退出',
            'csrf_token': generate_csrf()
        }), 200
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login')), 302

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return jsonify({
            'success': False,
            'message': '已登录',
            'csrf_token': generate_csrf()
        }), 400

    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({
            'success': False,
            'message': '用户名、密码和邮箱不能为空',
            'csrf_token': generate_csrf()
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'message': '用户名已存在',
            'csrf_token': generate_csrf()
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            'success': False,
            'message': '邮箱已存在',
            'csrf_token': generate_csrf()
        }), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '注册成功',
        'csrf_token': generate_csrf()
    }), 200 