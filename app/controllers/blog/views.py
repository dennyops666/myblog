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
from app.utils.markdown import clean_xss
from . import blog_bp

@blog_bp.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    sticky_posts = PostService.get_sticky_posts()
    posts = PostService.get_posts_by_page(page)
    categories = CategoryService.get_all_categories()
    tags = TagService.get_all_tags()
    recent_comments = CommentService.get_recent_comments()
    archives = PostService.get_archives()
    
    return render_template('blog/index.html',
                         sticky_posts=sticky_posts,
                         posts=posts,
                         categories=categories,
                         tags=tags,
                         recent_comments=recent_comments,
                         archives=archives)

@blog_bp.route('/post/<int:post_id>')
def post(post_id):
    """文章详情页"""
    post = PostService.get_post_by_id(post_id)
    if not post or post.status != 1:
        abort(404)
        
    # 获取评论
    page = request.args.get('page', 1, type=int)
    per_page = 10
    comments = CommentService.get_comments_by_post(post.id, page, per_page)
    
    # 获取相关文章
    related_posts = PostService.get_related_posts(post)
    
    return render_template('blog/post.html',
                         post=post,
                         comments=comments.items,
                         comment_count=comments.total,
                         pagination=comments,
                         related_posts=related_posts)

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def comment(post_id):
    """提交评论"""
    post = PostService.get_post_by_id(post_id)
    if not post or post.status != 1:
        abort(404)
        
    form = CommentForm()
    if form.validate_on_submit():
        try:
            # 清理XSS
            author_name = clean_xss(form.author_name.data)
            content = clean_xss(form.content.data)
            
            comment = CommentService.create_comment(
                post_id=post.id,
                author_name=author_name,
                author_email=form.author_email.data,
                content=content
            )
            
            flash('评论提交成功，等待审核', 'success')
            return redirect(url_for('blog.post', post_id=post.id))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash('评论提交失败，请稍后重试', 'danger')
            
    return redirect(url_for('blog.post', post_id=post.id))

@blog_bp.route('/archive')
def archive():
    """归档页面"""
    archive_type = request.args.get('type', 'time')  # 默认按时间线展示
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    page = request.args.get('page', 1, type=int)
    
    if archive_type == 'category' and category_id:
        # 按分类展示
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            flash('分类不存在', 'danger')
            return redirect(url_for('blog.archive'))
        posts = PostService.get_posts_by_category(category_id, page)
        template = 'blog/archive_category.html'
        title = f'分类：{category.name}'
        data = {'category': category, 'posts': posts}
    elif archive_type == 'tag' and tag_id:
        # 按标签展示
        tag = TagService.get_tag_by_id(tag_id)
        if not tag:
            flash('标签不存在', 'danger')
            return redirect(url_for('blog.archive'))
        posts = PostService.get_posts_by_tag(tag_id, page)
        template = 'blog/archive_tag.html'
        title = f'标签：{tag.name}'
        data = {'tag': tag, 'posts': posts}
    else:
        # 按时间线展示
        archives = PostService.get_archives()
        if year and month:
            # 展示特定年月的文章
            posts = PostService.get_posts_by_time(year, month, page)
            title = f'{year}年{month}月'
        else:
            # 展示所有文章的时间线
            posts = None
            title = '文章归档'
        template = 'blog/archive_time.html'
        data = {'archives': archives, 'posts': posts, 'year': year, 'month': month}
    
    return render_template(template, title=title, **data)

@blog_bp.route('/about')
def about():
    """关于页面"""
    return render_template('blog/about.html')

@blog_bp.route('/categories')
def categories():
    """分类列表页面"""
    categories = CategoryService.get_all_categories()
    return render_template('blog/categories.html', categories=categories)

@blog_bp.route('/tags')
def tags():
    """标签列表页面"""
    tags = TagService.get_all_tags()
    return render_template('blog/tags.html', tags=tags)

@blog_bp.route('/search')
def search():
    """搜索页面"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if not query:
        return redirect(url_for('blog.index'))
    
    # 使用 SQLAlchemy 的 or_ 进行多字段搜索
    search_query = or_(
        Post.title.ilike(f'%{query}%'),
        Post.content.ilike(f'%{query}%')
    )
    
    # 获取搜索结果
    pagination = PostService.search_posts(search_query, page, per_page)
    posts = pagination.items
    
    return render_template('blog/search.html',
                         query=query,
                         posts=posts,
                         pagination=pagination)

