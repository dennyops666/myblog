"""
文件名：views.py
描述：博客前台视图
作者：denny
创建日期：2025-02-16
"""

from flask import (
    render_template, request, redirect, url_for, flash, 
    Blueprint, abort, current_app, jsonify
)
from flask_login import current_user, login_user, logout_user, login_required
from app.services.post import PostService
from app.services.comment import CommentService
from app.services.category import CategoryService
from app.services.tag import TagService
from app.services.user import UserService
from app.forms import CommentForm
from app.forms.auth import LoginForm
from sqlalchemy import or_
from app.models.post import Post, PostStatus
from datetime import datetime, UTC
from app.extensions import db
import markdown2
from app.models.role import Permission

# 创建服务实例
post_service = PostService()
comment_service = CommentService()
category_service = CategoryService()
tag_service = TagService()
user_service = UserService()

blog_bp = Blueprint('blog', __name__, url_prefix='/blog')

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['POSTS_PER_PAGE']
    
    result = post_service.get_post_list(page, per_page)
    archives = post_service.get_archives()
    categories = category_service.get_all_categories()
    tags = tag_service.get_all_tags()
    
    return render_template('blog/index.html',
                         posts=result,
                         archives=archives,
                         categories=categories,
                         tags=tags)

@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    """文章详情页"""
    try:
        # 获取文章
        post = db.session.get(Post, post_id)
        if not post:
            current_app.logger.error(f"文章不存在: {post_id}")
            flash('文章不存在', 'error')
            return redirect(url_for('blog.index'))
        
        # 检查文章状态
        if post.status != PostStatus.PUBLISHED:
            current_app.logger.error(f"文章未发布: {post_id}")
            flash('文章不存在', 'error')
            return redirect(url_for('blog.index'))
        
        # 增加浏览量
        try:
            post_service.increment_views(post_id)
        except Exception as e:
            current_app.logger.error(f"更新浏览量失败: {str(e)}")
        
        # 获取上一篇和下一篇文章
        prev_post, next_post = post_service.get_prev_next_post(post)
        
        # 获取评论列表（只显示已审核的评论）
        try:
            comments = comment_service.get_comments_by_post_id(post_id, include_pending=False)
        except Exception as e:
            current_app.logger.error(f"获取评论列表失败: {str(e)}")
            comments = []
        
        # 确保 HTML 内容已生成
        if not post.html_content:
            post.html_content = markdown2.markdown(post.content, extras={
                'fenced-code-blocks': None,
                'tables': None,
                'header-ids': None,
                'toc': None,
                'footnotes': None,
                'metadata': None,
                'code-friendly': None
            })
            db.session.commit()
        
        # 创建评论表单
        form = CommentForm()
        
        return render_template('blog/post.html',
                             post=post,
                             prev_post=prev_post,
                             next_post=next_post,
                             comments=comments,
                             form=form)
                             
    except Exception as e:
        current_app.logger.error(f"获取文章详情失败: {str(e)}")
        flash('获取文章详情失败', 'error')
        return render_template('blog/error.html', error_message='获取文章详情失败'), 500

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': '无效的请求数据'}), 400
            
        content = data.get('content')
        nickname = data.get('nickname')
        email = data.get('email')
        parent_id = data.get('parent_id')
        
        # 获取当前用户ID（如果已登录）
        author_id = current_user.id if current_user.is_authenticated else None
        
        # 创建评论
        result = comment_service.create_comment(
            post_id=post_id,
            content=content,
            nickname=nickname,
            email=email,
            author_id=author_id,
            parent_id=parent_id
        )
        
        if result['status'] == 'success':
            # 返回成功响应
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'comment': {
                    'id': result['comment'].id,
                    'content': result['comment'].content,
                    'nickname': result['comment'].nickname or result['comment'].author.username if result['comment'].author else result['comment'].nickname,
                    'created_at': result['comment'].created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }), 201
        else:
            # 返回错误响应
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"创建评论失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': '创建评论失败'
        }), 500

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
@blog_bp.route('/archive/<date>')
def archive(date=None):
    """归档页面"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    if date:
        try:
            year, month = map(int, date.split('-'))
            result = post_service.get_posts_by_time(year, month, page, per_page)
        except ValueError:
            flash('无效的日期格式', 'danger')
            return redirect(url_for('blog.index'))
    else:
        result = post_service.get_posts_by_page(page, per_page)
        
    archives = post_service.get_archives()
    
    return render_template('blog/archive.html',
                         posts=result,
                         archives=archives,
                         year=year if date else None,
                         month=month if date else None)

@blog_bp.route('/login', methods=['GET', 'POST'])
def login():
    """博客前台登录"""
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = user_service.get_user_by_username(form.username.data)
        if user and user.verify_password(form.password.data):
            # 检查是否是管理员用户
            if user.is_admin:
                flash('管理员用户请从后台登录', 'warning')
                return redirect(url_for('auth.login'))
            
            # 普通用户登录
            login_user(user, remember=form.remember_me.data)
            flash('登录成功', 'success')
            
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('blog.index'))
            
        flash('用户名或密码错误', 'danger')
    
    return render_template('blog/login.html', form=form)

@blog_bp.route('/logout')
@login_required
def logout():
    """博客前台退出"""
    logout_user()
    flash('您已退出登录', 'success')
    return redirect(url_for('blog.index'))

