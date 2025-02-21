"""
文件名：blog.py
描述：博客控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, jsonify
from app.services import PostService, CategoryService, TagService
from app.models import Post, Category, Tag

blog_bp = Blueprint('blog', __name__)

post_service = PostService()
category_service = CategoryService()
tag_service = TagService()

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # 获取置顶文章
    sticky_posts = post_service.get_sticky_posts()
    
    # 获取普通文章
    pagination = post_service.get_posts_by_page(page, per_page)
    
    # 获取分类列表
    categories = category_service.get_categories_with_post_count()
    
    # 获取标签列表
    tags = tag_service.get_tags_with_post_count()
    
    return render_template('blog/index.html',
        sticky_posts=sticky_posts,
        posts=pagination.items,
        pagination=pagination,
        categories=categories,
        tags=tags
    )

@blog_bp.route('/category/<string:slug>')
def category(slug):
    """分类文章列表"""
    category = category_service.get_category_by_slug(slug)
    if not category:
        return render_template('errors/404.html'), 404
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = post_service.get_posts_by_category(
        category.id,
        page,
        per_page
    )
    
    return render_template('blog/category.html',
        category=category,
        posts=pagination.items,
        pagination=pagination
    )

@blog_bp.route('/tag/<string:slug>')
def tag(slug):
    """标签文章列表"""
    tag = tag_service.get_tag_by_slug(slug)
    if not tag:
        return render_template('errors/404.html'), 404
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = post_service.get_posts_by_tag(
        tag.id,
        page,
        per_page
    )
    
    return render_template('blog/tag.html',
        tag=tag,
        posts=pagination.items,
        pagination=pagination
    )

@blog_bp.route('/archive')
def archive():
    """文章归档"""
    posts = post_service.get_posts_by_time()
    return render_template('blog/archive.html', posts=posts)

@blog_bp.route('/search')
def search():
    """搜索文章"""
    keyword = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not keyword:
        return redirect(url_for('blog.index'))
        
    pagination = post_service.search_posts(keyword, page, per_page)
    
    return render_template('blog/search.html',
        keyword=keyword,
        posts=pagination.items,
        pagination=pagination
    ) 