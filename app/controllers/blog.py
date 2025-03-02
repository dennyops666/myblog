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
from app.models import Post, Category, Tag
from app.extensions import db

blog = Blueprint('blog', __name__)

def get_sidebar_data():
    """获取侧边栏所需的所有数据"""
    current_app.logger.info("获取侧边栏数据")
    
    try:
        # 获取所有分类及其文章数量
        categories = Category.query.all()
        category_post_counts = {}
        for category in categories:
            # 使用select查询获取文章数量
            count = Post.query.filter_by(
                category_id=category.id,
                published=True
            ).count()
            category_post_counts[category.id] = count
            current_app.logger.debug(f"分类 '{category.name}' 的文章数量: {count}")
        
        # 获取所有标签及其文章数量
        tags = Tag.query.all()
        tag_post_counts = {}
        for tag in tags:
            # 使用select查询获取文章数量
            count = Post.query.filter(
                Post.tags.contains(tag),
                Post.published == True
            ).count()
            tag_post_counts[tag.id] = count
            current_app.logger.debug(f"标签 '{tag.name}' 的文章数量: {count}")
        
        # 获取最新文章
        recent_posts = Post.query.filter_by(published=True).order_by(
            Post.created_at.desc()
        ).limit(5).all()
        
        current_app.logger.info(f"成功获取侧边栏数据: {len(categories)}个分类, {len(tags)}个标签, {len(recent_posts)}篇最新文章")
        
        return {
            'categories': categories,
            'tags': tags,
            'recent_posts': recent_posts,
            'category_post_counts': category_post_counts,
            'tag_post_counts': tag_post_counts
        }
    except Exception as e:
        current_app.logger.error(f"获取侧边栏数据失败: {str(e)}")
        return {
            'categories': [],
            'tags': [],
            'recent_posts': [],
            'category_post_counts': {},
            'tag_post_counts': {}
        }

@blog.route('/')
def index():
    """博客首页"""
    current_app.logger.info("访问博客首页")
    
    # 获取查询参数
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    
    current_app.logger.debug(f"查询参数: page={page}, search={search}, category_id={category_id}, tag_id={tag_id}")
    
    # 构建基础查询
    query = Post.query.filter_by(published=True)
    
    # 应用搜索过滤
    if search:
        query = query.filter(
            db.or_(
                Post.title.ilike(f'%{search}%'),
                Post.content.ilike(f'%{search}%')
            )
        )
        current_app.logger.debug(f"应用搜索过滤: {search}")
    
    # 应用分类过滤
    if category_id:
        query = query.filter_by(category_id=category_id)
        current_app.logger.debug(f"应用分类过滤: {category_id}")
    
    # 应用标签过滤
    if tag_id:
        tag = Tag.query.get(tag_id)
        if tag:
            query = query.filter(Post.tags.contains(tag))
            current_app.logger.debug(f"应用标签过滤: {tag_id}")
    
    # 按创建时间倒序排序并分页
    try:
        pagination = query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=current_app.config.get('POSTS_PER_PAGE', 10),
            error_out=False
        )
        posts = pagination.items
        current_app.logger.info(f"成功获取文章列表，共{len(posts)}篇文章")
    except Exception as e:
        current_app.logger.error(f"获取文章列表失败: {str(e)}")
        posts = []
        pagination = None
    
    # 获取侧边栏数据
    sidebar_data = get_sidebar_data()
    
    return render_template('blog/index.html',
                         posts=posts,
                         pagination=pagination,
                         search=search,
                         current_category_id=category_id,
                         current_tag_id=tag_id,
                         **sidebar_data)

@blog.route('/post/<int:post_id>')
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
                         next_post=next_post,
                         **get_sidebar_data())

@blog.route('/archive/<date>')
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
                         month=month,
                         **get_sidebar_data())

@blog.route('/about')
def about():
    """关于页面"""
    return render_template('blog/about.html', **get_sidebar_data())

@blog.route('/post/<int:post_id>/comment', methods=['POST'])
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

@blog.route('/category/<int:category_id>')
def category(category_id):
    """分类页面"""
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(category=category, published=True).order_by(Post.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('blog/category.html', category=category, posts=posts, pagination=pagination, **get_sidebar_data())

@blog.route('/tag/<int:tag_id>')
def tag(tag_id):
    """标签页面"""
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    pagination = tag.posts.filter_by(published=True).order_by(Post.created_at.desc()).paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    posts = pagination.items
    return render_template('blog/tag.html', tag=tag, posts=posts, pagination=pagination, **get_sidebar_data())

@blog.route('/search')
def search():
    """搜索页面"""
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    if q:
        pagination = Post.query.filter(
            Post.published == True,
            db.or_(
                Post.title.ilike(f'%{q}%'),
                Post.content.ilike(f'%{q}%')
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
    else:
        pagination = Post.query.filter_by(published=True).order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=current_app.config['POSTS_PER_PAGE'],
            error_out=False
        )
    posts = pagination.items
    return render_template('blog/search.html', q=q, posts=posts, pagination=pagination, **get_sidebar_data())
