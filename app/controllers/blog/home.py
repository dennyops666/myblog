"""
文件名：home.py
描述：博客首页控制器
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request
from app.services import PostService, CategoryService
from . import blog_bp

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    posts = PostService.get_posts_by_page(page)
    categories = CategoryService.get_all_categories()
    return render_template('blog/index.html', posts=posts, categories=categories)

@blog_bp.route('/about')
def about():
    """关于页面"""
    return render_template('blog/about.html') 