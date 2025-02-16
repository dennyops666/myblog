"""
文件名：views.py
描述：博客前台视图
作者：denny
创建日期：2025-02-16
"""

from flask import render_template, request, redirect, url_for, flash
from app.services import PostService, CommentService, CategoryService, TagService
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
    if not post:
        flash('文章不存在', 'danger')
        return redirect(url_for('blog.index'))
    
    # 获取相关文章
    related_posts = PostService.get_related_posts(post)
    # 获取上一篇和下一篇文章
    prev_post, next_post = PostService.get_prev_next_post(post)
    # 获取文章评论
    comments = CommentService.get_comments_by_post(post_id)
    
    return render_template('blog/post.html',
                         post=post,
                         related_posts=related_posts,
                         prev_post=prev_post,
                         next_post=next_post,
                         comments=comments)

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    post = PostService.get_post_by_id(post_id)
    if not post:
        flash('文章不存在', 'danger')
        return redirect(url_for('blog.index'))
    
    nickname = request.form.get('nickname')
    email = request.form.get('email')
    content = request.form.get('content')
    parent_id = request.form.get('parent_id', type=int)
    
    if not all([nickname, email, content]):
        flash('请填写所有必填字段', 'danger')
    else:
        try:
            CommentService.create_comment(
                post_id=post_id,
                nickname=nickname,
                email=email,
                content=content,
                parent_id=parent_id
            )
            flash('评论提交成功', 'success')
        except Exception as e:
            flash(f'评论提交失败：{str(e)}', 'danger')
    
    return redirect(url_for('blog.post', post_id=post_id))

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

