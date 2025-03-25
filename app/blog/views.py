from flask import render_template, request, redirect, url_for, flash, current_app, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Post, Tag, User, Category, Comment, PostStatus
from app.blog import blog
from app.utils import get_current_date
from app.forms import LoginForm, RegisterForm, CommentForm
from app.extensions import db
import datetime
from sqlalchemy import extract
from sqlalchemy.sql import func

@blog.route('/')
def index():
    """博客首页"""
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 获取搜索查询
    search_query = request.args.get('q', '')
    
    # 获取分类和标签过滤
    category_id = request.args.get('category_id', type=int)
    tag_id = request.args.get('tag_id', type=int)
    
    # 获取文章列表
    query = Post.query.filter_by(status=PostStatus.PUBLISHED)
    
    # 如果有搜索查询，过滤文章
    if search_query:
        search_filter = f"%{search_query}%"
        query = query.filter(Post.title.like(search_filter) | Post.content.like(search_filter))
    
    # 如果有分类过滤
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    # 如果有标签过滤
    if tag_id:
        tag = Tag.query.get_or_404(tag_id)
        query = query.filter(Post.tags.contains(tag))
    
    # 分页查询
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # 获取置顶文章
    sticky_posts = Post.query.filter_by(status=PostStatus.PUBLISHED, is_sticky=True).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类列表
    categories = Category.query.order_by(Category.name).all()
    
    # 获取标签列表
    tags = Tag.query.order_by(Tag.name).all()
    
    # 获取最新评论
    recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
    
    # 获取最新文章
    recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类文章数量
    category_post_counts = {}
    for category in categories:
        category_post_counts[category.id] = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
    
    # 获取标签文章数量
    tag_post_counts = {}
    for tag in tags:
        # 只计算已发布文章的数量
        published_posts = [post for post in tag.posts if post.status == PostStatus.PUBLISHED]
        tag_post_counts[tag.id] = len(published_posts)
    
    return render_template('blog/index.html', 
                          title='首页' if not search_query else f'搜索: {search_query}',
                          posts=posts.items,
                          pagination=posts,
                          sticky_posts=sticky_posts,
                          categories=categories,
                          tags=tags,
                          recent_comments=recent_comments,
                          recent_posts=recent_posts,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts,
                          current_category_id=category_id,
                          current_tag_id=tag_id,
                          search_query=search_query)

@blog.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('blog.index')
            flash('登录成功！', 'success')
            return redirect(next_page)
        flash('用户名或密码错误', 'danger')
    
    return render_template('blog/login.html', form=form)


@blog.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('blog.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        flash('注册成功，请登录', 'success')
        return redirect(url_for('blog.login'))
    
    return render_template('blog/register.html', form=form)


@blog.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('blog.login'))

@blog.route('/post/<int:post_id>')
def post_detail(post_id):
    """文章详情页"""
    post = Post.query.get_or_404(post_id)
    
    # 如果文章不是已发布状态，只有作者或管理员可以查看
    if post.status != PostStatus.PUBLISHED and (not current_user.is_authenticated or 
                                              (current_user.id != post.author_id and not current_user.is_admin)):
        abort(404)
    
    # 如果文章是私有的，只有作者或管理员可以查看
    if post.is_private and (not current_user.is_authenticated or 
                           (current_user.id != post.author_id and not current_user.is_admin)):
        abort(404)
    
    # 确保html_content字段被正确设置
    if not post.html_content and post.content:
        post.update_html_content()
        db.session.commit()
    
    # 增加浏览量
    post.view_count += 1
    db.session.commit()
    
    # 获取评论
    comments = Comment.query.filter_by(post_id=post_id, status=1).order_by(Comment.created_at.desc()).all()
    
    # 创建评论表单
    form = CommentForm()
    
    # 相关文章
    related_posts = Post.query.filter(
        Post.id != post_id,
        Post.status == PostStatus.PUBLISHED
    ).order_by(func.random()).limit(3).all()
    
    # 上一篇文章
    prev_post = Post.query.filter(
        Post.id < post_id,
        Post.status == PostStatus.PUBLISHED
    ).order_by(Post.id.desc()).first()
    
    # 下一篇文章
    next_post = Post.query.filter(
        Post.id > post_id,
        Post.status == PostStatus.PUBLISHED
    ).order_by(Post.id.asc()).first()
    
    # ===== 添加侧边栏数据 =====
    # 获取分类列表
    categories = Category.query.order_by(Category.name).all()
    
    # 获取标签列表
    tags = Tag.query.order_by(Tag.name).all()
    
    # 获取最新评论
    recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
    
    # 获取最新文章
    recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类文章数量
    category_post_counts = {}
    for category in categories:
        category_post_counts[category.id] = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
    
    # 获取标签文章数量
    tag_post_counts = {}
    for tag in tags:
        # 只计算已发布文章的数量
        published_posts = [post for post in tag.posts if post.status == PostStatus.PUBLISHED]
        tag_post_counts[tag.id] = len(published_posts)
    
    # 添加文章版本信息，用于调试
    
    # 添加错误处理
    try:
        # 获取版本信息，安全处理
        version_info = {
            'content_length': len(post.content or ''),
            'html_length': len(post.html_content or ''),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else 'N/A',
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') if 'datetime' in globals() else 'N/A'
        }
    except Exception as e:
        # 出错时使用安全的默认版本信息
        version_info = {
            'content_length': 0,
            'html_length': 0,
            'updated_at': 'N/A',
            'timestamp': 'N/A',
            'error': str(e)
        }
        

    
    return render_template('blog/post_detail.html',
                          title=post.title,
                          post=post,
                          comments=comments,
                          form=form,
                          related_posts=related_posts,
                          prev_post=prev_post,
                          next_post=next_post,
                          allow_comments=True,
                          # 添加侧边栏数据
                          categories=categories,
                          tags=tags,
                          recent_comments=recent_comments,
                          recent_posts=recent_posts,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts,
                          version_info=version_info)  # 添加版本信息

@blog.route('/archive')
def archive():
    """归档页面"""
    # 按年月归档文章，同时显示已发布和已归档的文章
    posts = Post.query.filter(
        Post.status.in_([PostStatus.PUBLISHED, PostStatus.ARCHIVED])
    ).order_by(Post.created_at.desc()).all()
    
    # 创建归档字典
    archive_dict = {}
    for post in posts:
        year = post.created_at.year
        month = post.created_at.month
        
        if year not in archive_dict:
            archive_dict[year] = {}
        
        if month not in archive_dict[year]:
            archive_dict[year][month] = []
        
        archive_dict[year][month].append(post)
    
    # 按年份降序排序
    sorted_years = sorted(archive_dict.keys(), reverse=True)
    
    # ===== 添加侧边栏数据 =====
    # 获取分类列表
    categories = Category.query.order_by(Category.name).all()
    
    # 获取标签列表
    tags = Tag.query.order_by(Tag.name).all()
    
    # 获取最新评论
    recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
    
    # 获取最新文章
    recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类文章数量
    category_post_counts = {}
    for category in categories:
        category_post_counts[category.id] = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
    
    # 获取标签文章数量
    tag_post_counts = {}
    for tag in tags:
        # 只计算已发布文章的数量
        published_posts = [post for post in tag.posts if post.status == PostStatus.PUBLISHED]
        tag_post_counts[tag.id] = len(published_posts)
    
    return render_template('blog/archive.html',
                          title='归档',
                          archive_dict=archive_dict,
                          sorted_years=sorted_years,
                          # 添加侧边栏数据
                          categories=categories,
                          tags=tags,
                          recent_comments=recent_comments,
                          recent_posts=recent_posts,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts)

@blog.route('/about')
def about():
    """关于页面"""
    from datetime import datetime
    from app.models.post import Post, PostStatus
    from app.models.category import Category
    from app.models.tag import Tag
    from app.models.comment import Comment
    
    try:
        # 准备关于页面的数据
        about_data = {
            'blog_name': current_app.config.get('BLOG_NAME', 'MyBlog'),
            'blog_description': current_app.config.get('BLOG_DESCRIPTION', '这是一个基于Flask的个人博客系统'),
            'author': current_app.config.get('BLOG_AUTHOR', 'Admin'),
            'created_at': current_app.config.get('BLOG_CREATED_AT', '2024'),
            'github': current_app.config.get('GITHUB_URL', 'https://github.com'),
            'email': current_app.config.get('CONTACT_EMAIL', 'admin@example.com'),
            # 统计数据 - 使用安全的计数方式
            'post_count': Post.query.filter(Post.status == PostStatus.PUBLISHED).count(),
            'category_count': Category.query.count(),
            'tag_count': Tag.query.count(),
            'comment_count': Comment.query.filter_by(status=1).count(),
            # 当前年份
            'current_year': datetime.now().year
        }
        
        # 简化侧边栏数据获取，避免出错
        # 获取分类列表
        categories = Category.query.order_by(Category.name).all()
        
        # 获取标签列表
        tags = Tag.query.order_by(Tag.name).all()
        
        # 获取最新评论 - 使用安全的方式
        try:
            recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
        except Exception:
            current_app.logger.exception("获取最新评论失败")
            recent_comments = []
        
        # 获取最新文章 - 使用安全的方式
        try:
            recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
        except Exception:
            current_app.logger.exception("获取最新文章失败")
            recent_posts = []
        
        # 获取分类文章数量 - 使用安全的方式
        category_post_counts = {}
        for category in categories:
            try:
                count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
                category_post_counts[category.id] = count
            except Exception:
                category_post_counts[category.id] = 0
        
        # 获取标签文章数量 - 使用安全的方式
        tag_post_counts = {}
        for tag in tags:
            try:
                # 只计算已发布文章的数量
                published_posts = [post for post in tag.posts if post.status == PostStatus.PUBLISHED]
                tag_post_counts[tag.id] = len(published_posts)
            except Exception:
                tag_post_counts[tag.id] = 0
        
        # 调试信息
        current_app.logger.info(f"关于页面数据准备完成")
        
        # 使用默认的错误处理模板
        if not hasattr(current_app, 'jinja_env') or not current_app.jinja_env.get_template('blog/about.html'):
            raise Exception("模板文件不存在")
        
        # 渲染模板，确保所有变量都传递正确
        return render_template('blog/about.html', 
                               about=about_data, 
                               now=datetime.now(),
                               # 添加侧边栏数据
                               categories=categories,
                               tags=tags,
                               recent_comments=recent_comments,
                               recent_posts=recent_posts,
                               category_post_counts=category_post_counts,
                               tag_post_counts=tag_post_counts)
    except Exception as e:
        current_app.logger.error(f"加载关于页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        # 使用简化的错误模板
        return render_template('blog/error.html', error_message='加载关于页面时发生错误，请联系管理员'), 500

@blog.route('/category/<int:category_id>')
def category_posts(category_id):
    """分类文章列表"""
    category = Category.query.get_or_404(category_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 获取该分类下的文章
    query = Post.query.filter_by(category_id=category_id, status=PostStatus.PUBLISHED)
    
    # 分页查询
    posts = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # 获取置顶文章
    sticky_posts = Post.query.filter_by(status=PostStatus.PUBLISHED, is_sticky=True, category_id=category_id).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类列表
    categories = Category.query.order_by(Category.name).all()
    
    # 获取标签列表
    tags = Tag.query.order_by(Tag.name).all()
    
    # 获取最新评论
    recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
    
    # 获取最新文章
    recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类文章数量
    category_post_counts = {}
    for cat in categories:
        category_post_counts[cat.id] = Post.query.filter_by(category_id=cat.id, status=PostStatus.PUBLISHED).count()
    
    # 获取标签文章数量
    tag_post_counts = {}
    for tag in tags:
        # 只计算已发布文章的数量
        published_posts = [post for post in tag.posts if post.status == PostStatus.PUBLISHED]
        tag_post_counts[tag.id] = len(published_posts)
    
    return render_template('blog/index.html',
                          title=f'分类: {category.name}',
                          posts=posts.items,
                          pagination=posts,
                          sticky_posts=sticky_posts,
                          categories=categories,
                          tags=tags,
                          recent_comments=recent_comments,
                          recent_posts=recent_posts,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts,
                          current_category_id=category_id,
                          current_tag_id=None,
                          search_query=None)

@blog.route('/tag/<int:tag_id>')
def tag_posts(tag_id):
    """标签文章列表"""
    tag = Tag.query.get_or_404(tag_id)
    
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 获取该标签下的文章
    posts_query = Post.query.join(Post.tags).filter(
        Tag.id == tag_id,
        Post.status == PostStatus.PUBLISHED
    )
    
    # 分页查询
    posts = posts_query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # 获取置顶文章
    sticky_posts = Post.query.filter_by(status=PostStatus.PUBLISHED, is_sticky=True).join(Post.tags).filter(Tag.id == tag_id).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类列表
    categories = Category.query.order_by(Category.name).all()
    
    # 获取标签列表
    tags = Tag.query.order_by(Tag.name).all()
    
    # 获取最新评论
    recent_comments = Comment.query.filter_by(status=1).order_by(Comment.created_at.desc()).limit(5).all()
    
    # 获取最新文章
    recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
    
    # 获取分类文章数量
    category_post_counts = {}
    for category in categories:
        category_post_counts[category.id] = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
    
    # 获取标签文章数量
    tag_post_counts = {}
    for t in tags:
        # 只计算已发布文章的数量
        published_posts = [post for post in t.posts if post.status == PostStatus.PUBLISHED]
        tag_post_counts[t.id] = len(published_posts)
    
    return render_template('blog/index.html',
                          title=f'标签: {tag.name}',
                          posts=posts.items,
                          pagination=posts,
                          sticky_posts=sticky_posts,
                          categories=categories,
                          tags=tags,
                          recent_comments=recent_comments,
                          recent_posts=recent_posts,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts,
                          current_category_id=None,
                          current_tag_id=tag_id,
                          search_query=None)

@blog.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    post = Post.query.get_or_404(post_id)
    
    # 检查文章是否允许评论
    if not post.can_comment:
        return jsonify({
            'status': 'error',
            'message': '该文章不允许评论'
        }), 403
    
    # 获取评论数据
    data = request.get_json()
    
    if not data:
        return jsonify({
            'status': 'error',
            'message': '无效的请求数据'
        }), 400
    
    nickname = data.get('nickname')
    email = data.get('email')
    content = data.get('content')
    
    if not nickname or not content:
        return jsonify({
            'status': 'error',
            'message': '昵称和评论内容不能为空'
        }), 400
    
    # 创建评论
    comment = Comment(
        post_id=post_id,
        nickname=nickname,
        email=email,
        content=content,
        status=1  # 直接设置为已审核状态
    )
    
    db.session.add(comment)
    
    # 更新文章评论数
    post._comments_count = post._comments_count + 1 if post._comments_count else 1
    
    db.session.commit()
    
    # 返回评论数据
    return jsonify({
        'status': 'success',
        'message': '评论发布成功',
        'comment': {
            'id': comment.id,
            'nickname': comment.nickname,
            'email': comment.email,
            'content': comment.content,
            'html_content': comment.html_content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    }) 