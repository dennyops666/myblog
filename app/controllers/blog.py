"""
文件名：blog.py
描述：博客控制器
作者：denny
创建日期：2024-03-21
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from app.services.post import PostService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.comment import CommentService
from app.models.post import PostStatus
from flask_login import current_user

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    post_service = PostService()
    category_service = CategoryService()
    tag_service = TagService()
    
    posts = post_service.get_posts_by_page(page, per_page)
    archives = post_service.get_archives()
    categories = category_service.get_all_categories()
    tags = tag_service.get_all_tags()
    
    return render_template('blog/index.html', 
                         posts=posts,
                         archives=archives,
                         categories=categories,
                         tags=tags)

@blog_bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """文章详情页"""
    post_service = PostService()
    post = post_service.get_post(post_id)
    
    if not post:
        flash('文章不存在')
        return redirect(url_for('blog.index'))
        
    # 增加浏览量
    post_service.increment_views(post_id)
    
    # 获取相关文章
    related_posts = post_service.get_related_posts(post)
    
    # 获取上一篇和下一篇文章
    prev_post, next_post = post_service.get_prev_next_post(post)
    
    return render_template('blog/post.html',
                         post=post,
                         related_posts=related_posts,
                         prev_post=prev_post,
                         next_post=next_post)

@blog_bp.route('/archive/<date>')
def archive(date):
    """归档页面"""
    try:
        year, month = map(int, date.split('-'))
    except ValueError:
        flash('无效的日期格式', 'error')
        return redirect(url_for('blog.index'))
        
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    post_service = PostService()
    posts = post_service.get_posts_by_time(year, month, page, per_page)
    archives = post_service.get_archives()
    
    return render_template('blog/archive.html',
                         posts=posts,
                         archives=archives,
                         year=year,
                         month=month)

@blog_bp.route('/about')
def about():
    """关于页面"""
    return render_template('blog/about.html')

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    content = request.form.get('content')
    nickname = request.form.get('nickname')
    email = request.form.get('email')
    parent_id = request.form.get('parent_id', type=int)
    
    if not content:
        flash('评论内容不能为空')
        return redirect(url_for('blog.post_detail', post_id=post_id))
    
    comment_service = CommentService()
    try:
        comment = comment_service.create_comment(
            content=content,
            post_id=post_id,
            author_id=current_user.id if current_user.is_authenticated else None,
            parent_id=parent_id,
            nickname=nickname,
            email=email
        )
        flash('评论发表成功')
    except Exception as e:
        current_app.logger.error(f"创建评论失败: {str(e)}")
        flash('评论发表失败')
    
    return redirect(url_for('blog.post_detail', post_id=post_id)) 