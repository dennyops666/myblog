"""
文件名：auth.py
描述：认证控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.services import UserService
from app.models import User

auth_bp = Blueprint('auth', __name__)
user_service = UserService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not all([username, password]):
            return jsonify({'error': '请填写所有必填字段'}), 400
            
        user = user_service.get_user_by_username(username)
        if user and user_service.verify_password(user.id, password):
            login_user(user, remember=remember)
            return jsonify({'message': '登录成功'})
        else:
            return jsonify({'error': '用户名或密码错误'}), 400
            
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    return jsonify({'message': '登出成功'}) 