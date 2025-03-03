"""
文件名：__init__.py
描述：管理后台蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, current_app
from flask_login import current_user, logout_user, login_required, login_user
from flask_wtf.csrf import generate_csrf
from app.services import UserService, OperationLogService
from datetime import datetime, UTC
from app.models.user import User
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment
from app.extensions import db
from app.forms.admin import PostForm, CategoryForm, TagForm, ProfileForm, LoginForm
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.comment import CommentService
from app.controllers.admin.user import bp as user_bp
from app.controllers.admin.post import post_bp
from app.controllers.admin.category import category_bp
from app.controllers.admin.tag import tag_bp
from app.controllers.admin.comment import comment_bp
from .upload import upload_bp
from functools import wraps
from urllib.parse import urlparse
from app.decorators import admin_required
from app.middleware.security import xss_protect, sql_injection_protect
from app.models.permission import Permission

# 创建蓝图
admin_bp = Blueprint('admin', __name__)

# 初始化服务
user_service = UserService()
post_service = PostService()
category_service = CategoryService()
tag_service = TagService()
comment_service = CommentService()
operation_log_service = OperationLogService()

# 注册子蓝图
admin_bp.register_blueprint(user_bp, url_prefix='/users')
admin_bp.register_blueprint(post_bp, url_prefix='/posts')
admin_bp.register_blueprint(category_bp, url_prefix='/categories')
admin_bp.register_blueprint(tag_bp, url_prefix='/tags')
admin_bp.register_blueprint(comment_bp, url_prefix='/comments')
admin_bp.register_blueprint(upload_bp, url_prefix='/upload')

# 为所有视图函数添加安全保护
for endpoint in admin_bp.view_functions:
    admin_bp.view_functions[endpoint] = xss_protect()(
        sql_injection_protect()(admin_bp.view_functions[endpoint])
    )

def check_auth():
    if not current_user.is_authenticated:
        if request.is_json:
            return {'success': False, 'message': '请先登录'}, 401
        return redirect(url_for('auth.login', next=request.url))
    return None

@admin_bp.before_request
def require_login():
    if request.endpoint and 'static' in request.endpoint:
        return
    if not current_user.is_authenticated:
        if request.is_json:
            return jsonify({'error': '请先登录'}), 401
        return redirect(url_for('auth.login', next=request.url))

@admin_bp.route('/')
@login_required
@admin_required
def index():
    """管理后台首页"""
    return render_template('admin/index.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        # 验证用户名和密码
        result = user_service.validate_admin_login(username, password)
        if result['status']:
            user = result['user']
            login_user(user, remember=remember)
            
            # 记录操作日志
            operation_log_service.log_operation(
                user=user,
                action='登录',
                details='管理员登录'
            )
            
            return jsonify({
                'success': True,
                'message': '登录成功',
                'redirect_url': url_for('admin.index')
            })
        else:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            })
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """退出登录"""
    # 记录操作日志
    operation_log_service.log_operation(
        user=current_user,
        action='退出登录',
        details='管理员退出登录'
    )
    
    logout_user()
    return jsonify({
        'success': True,
        'message': '已安全退出',
        'redirect_url': url_for('admin.login')
    })

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料"""
    # 创建表单对象
    form = ProfileForm(obj=current_user)
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            user_service.update_user(
                user_id=current_user.id,
                username=username,
                email=email,
                password=password
            )
            return jsonify({
                'success': True,
                'message': '个人资料更新成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': str(e)
            })
            
    return render_template('admin/profile.html', user=current_user, form=form)
