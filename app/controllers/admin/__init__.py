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
from .post import post_bp
from app.controllers.admin.category import category_bp
from app.controllers.admin.tag import tag_bp
from app.controllers.admin.comment import comment_bp
from app.controllers.admin.user import user_bp
from .upload import upload_bp
from functools import wraps
from urllib.parse import urlparse
from app.decorators import admin_required
from app.middleware.security import xss_protect, sql_injection_protect

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_service = UserService()
post_service = PostService()
category_service = CategoryService()
tag_service = TagService()
comment_service = CommentService()
operation_log_service = OperationLogService()

# 注册子蓝图
admin_bp.register_blueprint(post_bp, url_prefix='/posts')
admin_bp.register_blueprint(category_bp, url_prefix='/categories')
admin_bp.register_blueprint(tag_bp, url_prefix='/tags')
admin_bp.register_blueprint(comment_bp, url_prefix='/comments')
admin_bp.register_blueprint(user_bp, url_prefix='/users')
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
def index():
    """管理后台首页"""
    return render_template('admin/index.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """管理员登录"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = UserService.get_user_by_username(form.username.data)
        
        if user and user.verify_password(form.password.data):
            # 验证是否具有管理员权限
            has_admin_permission = False
            for role in user.roles:
                if role.permissions & (Permission.ADMIN.value | Permission.SUPER_ADMIN.value):
                    has_admin_permission = True
                    break
                    
            if not has_admin_permission:
                flash('您没有管理员权限', 'danger')
                return redirect(url_for('admin.login'))
                
            # 管理员登录成功
            login_user(user, remember=form.remember_me.data)
            
            # 记录登录操作
            operation_log_service.log_operation(
                user=user,
                action='admin_login',
                details=f'管理员 {user.username} 登录后台'
            )
            
            flash('登录成功', 'success')
            return redirect(url_for('admin.index'))
        else:
            flash('用户名或密码错误', 'danger')
            
    return render_template('admin/login.html', form=form)

@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """管理后台登出"""
    logout_user()
    flash('已安全退出', 'success')
    return redirect(url_for('auth.login'))

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """个人资料页面"""
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('个人资料更新成功', 'success')
        return redirect(url_for('admin.profile'))
    return render_template('admin/profile.html', form=form)
