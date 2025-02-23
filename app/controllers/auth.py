"""
文件名：auth.py
描述：认证控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('auth/login.html'), 200

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember)
            session['_fresh'] = True
            next_page = request.args.get('next', url_for('admin.index'))
            return redirect(next_page)
        else:
            flash('用户名或密码错误', 'danger')
            return render_template('auth/login.html'), 200

    return render_template('auth/login.html'), 200

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login')), 302

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': '已登录'}), 400

    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({'success': False, 'message': '用户名、密码和邮箱不能为空'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': '邮箱已存在'}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({'success': True, 'message': '注册成功'}) 