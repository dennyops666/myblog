"""
文件名：index.py
描述：管理后台首页控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, redirect, url_for
from flask_login import login_required, logout_user
from app.services import PostService, CategoryService, CommentService
from . import admin_bp

@admin_bp.route('/')
@login_required
def index():
    """管理后台首页"""
    # 获取统计数据
    total_posts = PostService.get_total_posts()
    total_categories = CategoryService.get_total_categories()
    pending_comments = CommentService.get_total_pending_comments()
    recent_posts = PostService.get_recent_posts(limit=5)
    
    return render_template('admin/index.html',
                         total_posts=total_posts,
                         total_categories=total_categories,
                         pending_comments=pending_comments,
                         recent_posts=recent_posts)

@admin_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """退出登录"""
    logout_user()
    return redirect(url_for('admin.index')) 