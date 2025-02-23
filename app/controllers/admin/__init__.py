"""
文件名：__init__.py
描述：管理后台蓝图初始化
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, current_app
from flask_login import current_user, logout_user, login_required, login_user
from flask_wtf.csrf import generate_csrf
from app.services import UserService
from datetime import datetime, UTC
from app.models.user import User
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment
from app.extensions import db
from app.forms.admin import PostForm, CategoryForm, TagForm, ProfileForm
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.comment import CommentService
from app.controllers.admin.post import post_bp
from app.controllers.admin.category import category_bp
from app.controllers.admin.tag import tag_bp
from app.controllers.admin.comment import comment_bp
from app.controllers.admin.user import user_bp
from app.controllers.admin.upload import upload_bp
from functools import wraps

# 创建蓝图
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
user_service = UserService()
post_service = PostService()
category_service = CategoryService()
tag_service = TagService()
comment_service = CommentService()

# 注册子蓝图
admin_bp.register_blueprint(post_bp)
admin_bp.register_blueprint(category_bp)
admin_bp.register_blueprint(tag_bp)
admin_bp.register_blueprint(comment_bp)
admin_bp.register_blueprint(user_bp)
admin_bp.register_blueprint(upload_bp)

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

@admin_bp.route('/login')
def login():
    """管理后台登录页面"""
    if current_user.is_authenticated:
        return redirect(url_for('admin.index'))
    return redirect(url_for('auth.login', next=url_for('admin.index')))

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

@admin_bp.route('/upload/', methods=['GET', 'POST'])
@login_required
def upload():
    """文件上传页面"""
    if request.method == 'GET':
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                'success': True, 
                'message': '准备上传',
                'csrf_token': generate_csrf()
            }), 200
        return render_template('admin/upload.html'), 200
    return redirect(url_for('admin.index'))
