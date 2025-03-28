"""
文件名：blog.py
描述：博客视图
作者：denny
"""

from flask import Blueprint, render_template, request, jsonify, abort, current_app, url_for, flash, redirect, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app.models.post import Post, PostStatus
from app.models.comment import Comment, CommentStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.user import User
from app.extensions import db
from datetime import datetime, UTC
from sqlalchemy import desc, func
import re
from werkzeug.security import generate_password_hash, check_password_hash
from zoneinfo import ZoneInfo
from datetime import timezone as tz

bp = Blueprint('blog', __name__, url_prefix='/blog')

@bp.route('/')
def index():
    """博客首页"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config.get('POSTS_PER_PAGE', 10)
        
        # 查询已发布的文章
        query = Post.query.filter_by(status=PostStatus.PUBLISHED)
        
        # 获取置顶文章
        sticky_posts = query.filter_by(is_sticky=True).order_by(Post.created_at.desc()).all()
        
        # 获取普通文章（分页）
        pagination = query.filter_by(is_sticky=False).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        posts = pagination.items
        
        # 获取分类和标签（用于侧边栏）
        categories = Category.query.all()
        tags = Tag.query.all()
        
        # 获取最新评论
        recent_comments = Comment.query.filter_by(status=CommentStatus.APPROVED).order_by(Comment.created_at.desc()).limit(5).all()
        
        # 获取最新文章
        recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
        
        # 计算每个分类下的文章数量
        category_post_counts = {}
        for category in categories:
            count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
            category_post_counts[category.id] = count
        
        # 计算每个标签下的文章数量
        tag_post_counts = {}
        for tag in tags:
            count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
            tag_post_counts[tag.id] = count
        
        return render_template('blog/index.html', 
                              title='博客首页',
                              sticky_posts=sticky_posts,
                              posts=posts,
                              pagination=pagination,
                              categories=categories,
                              tags=tags,
                              category_post_counts=category_post_counts,
                              tag_post_counts=tag_post_counts,
                              recent_comments=recent_comments,
                              recent_posts=recent_posts)
    except Exception as e:
        current_app.logger.error(f"首页加载错误: {str(e)}")
        return render_template('blog/error.html', title='错误', message='加载博客首页时发生错误'), 500

@bp.route('/about')
def about():
    """关于页面"""
    try:
        # 准备about变量
        from app.models.post import Post, PostStatus
        from app.models.category import Category
        from app.models.tag import Tag
        from app.models.comment import Comment, CommentStatus
        
        # 统计数据
        post_count = Post.query.filter_by(status=PostStatus.PUBLISHED).count()
        category_count = Category.query.count()
        tag_count = Tag.query.count()
        comment_count = Comment.query.filter_by(status=CommentStatus.APPROVED).count()
        
        # 构建about对象
        about_data = {
            'blog_name': current_app.config.get('BLOG_NAME', 'MyBlog'),
            'blog_description': '欢迎来到我的博客！这是一个使用Flask开发的个人博客系统，用于展示文章、分享知识和记录生活。',
            'post_count': post_count,
            'category_count': category_count, 
            'tag_count': tag_count,
            'comment_count': comment_count,
            'author': 'Admin',
            'created_at': '2024-03-21',
            'email': 'admin@example.com',
            'github': 'https://github.com',
            'current_year': datetime.now(UTC).year
        }
        
        # 获取分类和标签（用于侧边栏）
        categories = Category.query.all()
        tags = Tag.query.all()
        
        # 计算每个分类下的文章数量
        category_post_counts = {}
        for category in categories:
            count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
            category_post_counts[category.id] = count
        
        # 计算每个标签下的文章数量
        tag_post_counts = {}
        for tag in tags:
            count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
            tag_post_counts[tag.id] = count
        
        return render_template('blog/about.html', 
                              title='关于', 
                              about=about_data,
                              categories=categories,
                              tags=tags,
                              category_post_counts=category_post_counts,
                              tag_post_counts=tag_post_counts,
                              now=datetime.now(UTC))
    except Exception as e:
        current_app.logger.error(f"关于页面加载错误: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', title='错误', message='加载关于页面时发生错误'), 500

@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    """文章详情页"""
    try:
        # 强制从数据库获取最新数据，不使用缓存
        db.session.expire_all()
        
        # 记录请求详情
        current_app.logger.info(f"访问文章详情 - ID: {post_id}, IP: {request.remote_addr}")
        
        # 使用 joinedload 预加载关联数据
        post = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.tags),
            db.joinedload(Post.author)
        ).get_or_404(post_id)
        
        # 记录文章的内容状态
        content_len = len(post.content) if post.content else 0
        html_len = len(post.html_content) if post.html_content else 0
        current_app.logger.info(f"文章内容状态 - ID: {post_id}, 内容长度: {content_len}, HTML长度: {html_len}")
        
        # 如果HTML内容为空，强制更新
        if not post.html_content and post.content:
            current_app.logger.info(f"文章详情页：文章 {post_id} 的HTML内容为空，进行强制更新")
            try:
                # 确保修改保存到数据库
                post.update_html_content()
                db.session.refresh(post)
                current_app.logger.info(f"更新后HTML内容长度: {len(post.html_content or '')}")
            except Exception as e:
                current_app.logger.error(f"文章详情页：更新文章 {post_id} 的HTML内容失败: {str(e)}")
        
        # 如果文章未发布或为私有，且用户不是作者或管理员，则返回404
        if (post.status != PostStatus.PUBLISHED or post.is_private) and (
                not current_user.is_authenticated or 
                (current_user.id != post.author_id and not current_user.is_admin)):
            abort(404)
        
        # 获取上一篇和下一篇文章
        prev_post = Post.query.filter(
            Post.status == PostStatus.PUBLISHED,
            Post.created_at < post.created_at
        ).order_by(Post.created_at.desc()).first()
        
        next_post = Post.query.filter(
            Post.status == PostStatus.PUBLISHED,
            Post.created_at > post.created_at
        ).order_by(Post.created_at.asc()).first()
        
        # 获取文章评论
        comments = Comment.query.filter_by(post_id=post_id, status=CommentStatus.APPROVED).order_by(Comment.created_at.asc()).all()
        
        # 获取相关文章
        if post.category:
            related_posts = Post.query.filter(
                Post.category_id == post.category_id,
                Post.id != post.id,
                Post.status == PostStatus.PUBLISHED
            ).order_by(Post.created_at.desc()).limit(3).all()
        else:
            related_posts = []
        
        # 更新文章浏览量
        try:
            post.view_count = (post.view_count or 0) + 1
            db.session.commit()
            current_app.logger.info(f"文章 {post_id} 浏览量更新为: {post.view_count}")
        except Exception as e:
            current_app.logger.error(f"更新文章浏览量失败: {str(e)}")
            db.session.rollback()
        
        # 获取最新文章（用于侧边栏）
        recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
        
        # 获取分类和标签（用于侧边栏）
        categories = Category.query.all()
        tags = Tag.query.all()
        
        # 计算每个分类下的文章数量
        category_post_counts = {}
        for category in categories:
            count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
            category_post_counts[category.id] = count
        
        # 计算每个标签下的文章数量
        tag_post_counts = {}
        for tag in tags:
            count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
            tag_post_counts[tag.id] = count
        
        # 添加文章版本信息，用于调试
        version_info = {
            'content_length': len(post.content or ''),
            'html_length': len(post.html_content or ''),
            'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else 'N/A',
            'timestamp': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 清除响应缓存
        response = make_response(render_template('blog/post_detail.html', 
                            title=post.title,
                            post=post, 
                            prev_post=prev_post, 
                            next_post=next_post,
                            comments=comments,
                            related_posts=related_posts,
                            categories=categories,
                            tags=tags,
                            recent_posts=recent_posts,
                            category_post_counts=category_post_counts,
                            tag_post_counts=tag_post_counts,
                            version_info=version_info))
        
        # 设置响应头，禁止缓存
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Post-Version'] = f"c:{content_len}-h:{html_len}-t:{version_info['timestamp']}"
        
        return response
    except Exception as e:
        current_app.logger.error(f"加载文章详情页错误: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', title='错误', message='加载文章详情页时发生错误'), 500

@bp.route('/archive')
def archive():
    """归档页面"""
    try:
        # 获取所有已发布的文章
        posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).all()
        
        # 按年月分组
        archive_dict = {}
        for post in posts:
            year = post.created_at.year
            month = post.created_at.month
            if year not in archive_dict:
                archive_dict[year] = {}
            if month not in archive_dict[year]:
                archive_dict[year][month] = []
            archive_dict[year][month].append(post)
        
        # 排序
        sorted_years = sorted(archive_dict.keys(), reverse=True)
        archive_sorted = []
        for year in sorted_years:
            months = sorted(archive_dict[year].keys(), reverse=True)
            year_data = {'year': year, 'months': []}
            for month in months:
                month_posts = archive_dict[year][month]
                year_data['months'].append({
                    'month': month,
                    'posts': month_posts,
                    'count': len(month_posts)
                })
            archive_sorted.append(year_data)
        
        # 获取最新文章（用于侧边栏）
        recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
        
        # 获取分类和标签（用于侧边栏）
        categories = Category.query.all()
        tags = Tag.query.all()
        
        # 计算每个分类下的文章数量
        category_post_counts = {}
        for category in categories:
            count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
            category_post_counts[category.id] = count
        
        # 计算每个标签下的文章数量
        tag_post_counts = {}
        for tag in tags:
            count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
            tag_post_counts[tag.id] = count
        
        return render_template('blog/archive.html', 
                              title='文章归档',
                              archive=archive_sorted,
                              archive_dict=archive_dict,
                              sorted_years=sorted_years,
                              categories=categories,
                              tags=tags,
                              recent_posts=recent_posts,
                              category_post_counts=category_post_counts,
                              tag_post_counts=tag_post_counts)
    except Exception as e:
        current_app.logger.error(f"归档页面加载错误: {str(e)}")
        return render_template('blog/error.html', title='错误', message='加载归档页面时发生错误'), 500

@bp.route('/category/<int:category_id>')
def category_posts(category_id):
    """分类文章列表"""
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 查询该分类下的已发布文章
    pagination = Post.query.filter_by(
        category_id=category_id,
        status=PostStatus.PUBLISHED
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = pagination.items
    
    # 获取分类和标签（用于侧边栏）
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # 计算每个分类下的文章数量
    category_post_counts = {}
    for category in categories:
        count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
        category_post_counts[category.id] = count
    
    # 计算每个标签下的文章数量
    tag_post_counts = {}
    for tag in tags:
        count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
        tag_post_counts[tag.id] = count
    
    return render_template('blog/category_posts.html',
                          title=f'分类: {category.name}',
                          category=category,
                          posts=posts,
                          pagination=pagination,
                          categories=categories,
                          tags=tags,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts)

@bp.route('/tag/<int:tag_id>')
def tag_posts(tag_id):
    """标签文章列表"""
    tag = Tag.query.get_or_404(tag_id)
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    # 查询带有该标签的已发布文章
    pagination = Post.query.filter(
        Post.tags.any(id=tag_id),
        Post.status==PostStatus.PUBLISHED
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = pagination.items
    
    # 获取分类和标签（用于侧边栏）
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # 计算每个分类下的文章数量
    category_post_counts = {}
    for category in categories:
        count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
        category_post_counts[category.id] = count
    
    # 计算每个标签下的文章数量
    tag_post_counts = {}
    for tag in tags:
        count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
        tag_post_counts[tag.id] = count
    
    return render_template('blog/tag_posts.html',
                          title=f'标签: {tag.name}',
                          tag=tag,
                          posts=posts,
                          pagination=pagination,
                          categories=categories,
                          tags=tags,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts)

@bp.route('/search')
def search():
    """搜索文章"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('POSTS_PER_PAGE', 10)
    
    if not query:
        return redirect(url_for('blog.index'))
    
    # 简单搜索实现
    search_query = f"%{query}%"
    pagination = Post.query.filter(
        Post.status==PostStatus.PUBLISHED,
        (Post.title.like(search_query) | Post.content.like(search_query))
    ).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    posts = pagination.items
    
    # 获取分类和标签（用于侧边栏）
    categories = Category.query.all()
    tags = Tag.query.all()
    
    # 计算每个分类下的文章数量
    category_post_counts = {}
    for category in categories:
        count = Post.query.filter_by(category_id=category.id, status=PostStatus.PUBLISHED).count()
        category_post_counts[category.id] = count
    
    # 计算每个标签下的文章数量
    tag_post_counts = {}
    for tag in tags:
        count = Post.query.filter(Post.tags.any(id=tag.id), Post.status==PostStatus.PUBLISHED).count()
        tag_post_counts[tag.id] = count
    
    return render_template('blog/search.html',
                          title=f'搜索: {query}',
                          query=query,
                          posts=posts,
                          pagination=pagination,
                          categories=categories,
                          tags=tags,
                          category_post_counts=category_post_counts,
                          tag_post_counts=tag_post_counts)

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    if not request.is_json:
        return jsonify({'success': False, 'message': '请求格式错误'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': '请求数据为空'}), 400
    
    # 获取评论内容
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'message': '评论内容不能为空'}), 400
    
    # 获取父评论ID
    parent_id = data.get('parent_id')
    
    # 获取作者信息
    author_id = current_user.id if current_user.is_authenticated else None
    nickname = data.get('nickname', '').strip() if not current_user.is_authenticated else None
    email = data.get('email', '').strip() if not current_user.is_authenticated else None
    
    # 记录详细的用户信息和身份验证状态，用于调试
    current_app.logger.debug(f"创建评论请求: post_id={post_id}, authenticated={current_user.is_authenticated}, author_id={author_id}, content={content[:20]}..., parent_id={parent_id}")
    
    # 记录用户信息，用于调试
    if current_user.is_authenticated:
        current_app.logger.info(f"已登录用户发表评论: user_id={current_user.id}, username={current_user.username}")
    else:
        current_app.logger.info(f"匿名用户发表评论: nickname={nickname}, email={email}")
    
    # 创建评论
    from app.services.comment import CommentService
    from app.models.comment import CommentStatus
    
    # 确保已登录用户的评论状态是已审核状态
    initial_status = CommentStatus.APPROVED if current_user.is_authenticated else CommentStatus.PENDING
    current_app.logger.info(f"初始设置评论状态: user_authenticated={current_user.is_authenticated}, initial_status={initial_status}")
    
    result = CommentService.create_comment(
        post_id=post_id,
        content=content,
        author_id=author_id,
        nickname=nickname,
        email=email,
        parent_id=parent_id
    )
    
    if result['success']:
        # 成功创建评论后，再次确保已登录用户的评论状态是已审核
        if current_user.is_authenticated and 'comment' in result and result['comment']['status'] != CommentStatus.APPROVED:
            current_app.logger.warning(f"发现已登录用户评论状态异常: comment_id={result['comment']['id']}, status={result['comment']['status']}")
            # 通过直接SQL更新确保状态正确
            from app.extensions import db
            db.session.execute(
                db.text("UPDATE comments SET status = :status WHERE id = :id"),
                {"status": int(CommentStatus.APPROVED), "id": result['comment']['id']}
            )
            db.session.commit()
            current_app.logger.info(f"已强制修正评论状态: comment_id={result['comment']['id']}, new_status={CommentStatus.APPROVED}")
            
            # 更新返回结果中的状态
            result['comment']['status'] = CommentStatus.APPROVED
            result['message'] = '评论发表成功'
        
        return jsonify({
            'success': True,
            'message': result['message'],
            'comment': result['comment']
        }), 201
    else:
        return jsonify({'success': False, 'message': result['message']}), 400

@bp.route('/test')
def test():
    """一个简单的测试路由"""
    return "Hello World from blog test route!"

@bp.route('/test2')
def test2():
    """另一个简单的测试路由"""
    return "Hello World from blog test route 2!"
