"""
文件名：views.py
描述：博客前台视图
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash, Blueprint, abort
from app.services import PostService, CommentService, CategoryService, TagService
from app.forms import CommentForm
from sqlalchemy import or_
from app.models import Post
from app.utils.markdown import MarkdownService
from . import blog_bp

# 创建服务实例
markdown_service = MarkdownService()
post_service = PostService()
comment_service = CommentService()
category_service = CategoryService()
tag_service = TagService()

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取文章列表
    pagination = post_service.get_post_list(page, per_page)
    posts = pagination.items
    
    # 获取分类和标签
    categories = category_service.get_all_categories()
    tags = tag_service.get_all_tags()
    
    return render_template('blog/index.html',
                         posts=posts,
                         pagination=pagination,
                         categories=categories,
                         tags=tags)

@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    """文章详情页"""
    post = post_service.get_post_by_id(post_id)
    if not post:
        abort(404)
    
    # 增加阅读次数
    post_service.increment_views(post_id)
    
    # 获取评论
    comments = comment_service.get_comments_by_post_id(post_id)
    
    # 评论表单
    form = CommentForm()
    
    return render_template('blog/post.html',
                         post=post,
                         comments=comments,
                         form=form)

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def comment(post_id):
    """添加评论"""
    form = CommentForm()
    if form.validate_on_submit():
        content = markdown_service.clean_xss(form.content.data)
        parent_id = form.parent_id.data
        
        # 创建评论
        comment = comment_service.create_comment(
            content=content,
            post_id=post_id,
            author_id=current_user.id,
            parent_id=parent_id if parent_id else None
        )
        
        if comment:
            flash('评论发表成功！', 'success')
        else:
            flash('评论发表失败！', 'danger')
            
    return redirect(url_for('blog.post', post_id=post_id))

@blog_bp.route('/category/<int:category_id>')
def category(category_id):
    """分类页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取分类下的文章
    pagination = post_service.get_posts_by_category(category_id, page, per_page)
    posts = pagination.items
    
    # 获取分类信息
    category = category_service.get_category_by_id(category_id)
    if not category:
        abort(404)
    
    return render_template('blog/category.html',
                         category=category,
                         posts=posts,
                         pagination=pagination)

@blog_bp.route('/tag/<int:tag_id>')
def tag(tag_id):
    """标签页面"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 获取标签下的文章
    pagination = post_service.get_posts_by_tag(tag_id, page, per_page)
    posts = pagination.items
    
    # 获取标签信息
    tag = tag_service.get_tag_by_id(tag_id)
    if not tag:
        abort(404)
    
    return render_template('blog/tag.html',
                         tag=tag,
                         posts=posts,
                         pagination=pagination)

@blog_bp.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not query:
        return redirect(url_for('blog.index'))
    
    # 搜索文章
    pagination = post_service.search_posts(query, page, per_page)
    posts = pagination.items
    
    return render_template('blog/search.html',
                         query=query,
                         posts=posts,
                         pagination=pagination)

@blog_bp.route('/about')
def about():
    """关于页面"""
    return render_template('blog/about.html')

@blog_bp.route('/categories')
def categories():
    """分类列表页面"""
    categories = category_service.get_all_categories()
    return render_template('blog/categories.html', categories=categories)

@blog_bp.route('/tags')
def tags():
    """标签列表页面"""
    tags = tag_service.get_all_tags()
    return render_template('blog/tags.html', tags=tags)

@blog_bp.route('/archive')
def archive():
    """归档页面"""
    archives = post_service.get_archives()
    return render_template('blog/archive.html', archives=archives)

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    form = CommentForm()
    if form.validate_on_submit():
        result = comment_service.create_comment(
            post_id=post_id,
            nickname=form.nickname.data,
            email=form.email.data,
            content=form.content.data
        )
        if result[0]:
            flash('评论发表成功', 'success')
        else:
            flash(f'评论发表失败：{result[1]}', 'danger')
    return redirect(url_for('blog.post', post_id=post_id))

