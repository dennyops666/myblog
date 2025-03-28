"""
文件名：views.py
描述：博客前台视图
作者：denny
"""

from flask import (
    render_template, request, redirect, url_for, flash, 
    abort, current_app, jsonify, session, make_response
)
from flask_login import current_user, login_user, logout_user, login_required
from app.services.post import PostService
from app.services.comment import CommentService
from app.services.tag import TagService
from app.services.user import UserService
from app.forms import CommentForm
from app.forms.auth import LoginForm
from sqlalchemy import or_, text
from datetime import datetime, UTC
from app.extensions import db
import markdown2
from app.models.role import Permission
from app.models.comment import Comment, CommentStatus
from app.models.tag import Tag
from app.models.category import Category
from app.models.post import Post, PostStatus
from app.utils.pagination import Pagination
from app.services.category import CategoryService
from . import blog_bp
from math import ceil

# 创建服务实例
post_service = PostService()
comment_service = CommentService()
category_service = CategoryService()
tag_service = TagService()
user_service = UserService()

@blog_bp.route('/')
def index():
    """博客首页"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['POSTS_PER_PAGE']
        
        # 使用SQL直接获取文章列表
        sql = text("""
            SELECT posts.id, posts.title, posts.content, posts.summary, posts.created_at, 
                  posts.updated_at, posts.category_id, posts.view_count, 
                  posts.status, categories.name as category_name, posts.is_sticky
            FROM posts
            LEFT JOIN categories ON posts.category_id = categories.id
            WHERE (posts.status IN ('PUBLISHED', 'published') OR posts.is_sticky = 1)
            ORDER BY posts.is_sticky DESC, posts.created_at DESC
            LIMIT :per_page OFFSET :offset
        """)
        
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 执行查询
        result = db.session.execute(sql, {'per_page': per_page, 'offset': offset})
        posts = []
        for row in result:
            # 转换行为字典
            post_dict = {}
            for column, value in row._mapping.items():
                post_dict[column] = value
                
            # 将字符串日期转换为datetime对象
            if 'created_at' in post_dict and post_dict['created_at'] and isinstance(post_dict['created_at'], str):
                try:
                    post_dict['created_at'] = datetime.strptime(post_dict['created_at'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        post_dict['created_at'] = datetime.strptime(post_dict['created_at'], '%Y-%m-%d')
                    except ValueError:
                        post_dict['created_at'] = datetime.now()
            
            if 'updated_at' in post_dict and post_dict['updated_at'] and isinstance(post_dict['updated_at'], str):
                try:
                    post_dict['updated_at'] = datetime.strptime(post_dict['updated_at'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        post_dict['updated_at'] = datetime.strptime(post_dict['updated_at'], '%Y-%m-%d')
                    except ValueError:
                        post_dict['updated_at'] = datetime.now()
            
            # 添加空的tags属性，防止模板中的错误
            post_dict['tags'] = []
            
            # 添加category属性
            if 'category_id' in post_dict and post_dict['category_id']:
                class CategoryLike:
                    def __init__(self, id, name):
                        self.id = id
                        self.name = name
                
                if 'category_name' in post_dict:
                    post_dict['category'] = CategoryLike(post_dict['category_id'], post_dict['category_name'])
                else:
                    post_dict['category'] = None
            else:
                post_dict['category'] = None
            
            # 获取文章的标签
            post_obj = db.session.get(Post, post_dict['id'])
            if post_obj:
                post_dict['tags'] = post_obj.tags
            
            posts.append(post_dict)
        
        # 获取总文章数
        count_sql = text("SELECT COUNT(*) FROM posts WHERE status IN ('PUBLISHED', 'published') OR is_sticky = 1")
        total = db.session.execute(count_sql).scalar()
        
        # 分离置顶文章和普通文章
        sticky_posts = []
        regular_posts = []
        
        for post in posts:
            # 将字符串"1"、数字1和True都识别为置顶
            is_sticky = False
            if 'is_sticky' in post:
                if isinstance(post['is_sticky'], bool):
                    is_sticky = post['is_sticky']
                elif isinstance(post['is_sticky'], (int, float)):
                    is_sticky = post['is_sticky'] > 0
                elif isinstance(post['is_sticky'], str):
                    is_sticky = post['is_sticky'].lower() in ('true', '1', 't', 'yes', 'y')
                
            if is_sticky:
                sticky_posts.append(post)
            else:
                regular_posts.append(post)
                
        posts = regular_posts
        
        # 创建自定义分页对象
        class SimplePagination:
            def __init__(self, page, per_page, total_count):
                self.page = page
                self.per_page = per_page
                self.total = total_count
                self.items = posts
            
            @property
            def pages(self):
                """总页数"""
                if self.per_page == 0 or self.total == 0:
                    return 0
                return int(ceil(self.total / float(self.per_page)))
            
            @property
            def has_prev(self):
                """是否有上一页"""
                return self.page > 1
            
            @property
            def has_next(self):
                """是否有下一页"""
                return self.page < self.pages
                
            @property
            def prev_num(self):
                """上一页页码"""
                return self.page - 1 if self.has_prev else None
                
            @property
            def next_num(self):
                """下一页页码"""
                return self.page + 1 if self.has_next else None
            
            def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
                """迭代页码"""
                last = 0
                for num in range(1, self.pages + 1):
                    if num <= left_edge or \
                       (num > self.page - left_current - 1 and num < self.page + right_current) or \
                       num > self.pages - right_edge:
                        if last + 1 != num:
                            yield None
                        yield num
                        last = num
        
        # 使用自定义的分页类
        pagination = SimplePagination(page, per_page, total)
        
        # 不再调用 post_service.get_archives()，直接使用空字典
        archives = {}
        categories = category_service.get_all_categories()
        
        # 获取每个分类的文章数量
        category_post_counts = {}
        for category in categories:
            try:
                query = Post.query.filter(
                    Post.category_id == category.id,
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                category_post_counts[category.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取分类 {category.id} 的文章数量失败: {str(e)}")
                category_post_counts[category.id] = 0
        
        current_app.logger.info("正在获取标签列表...")
        tags = tag_service.get_all_tags()
        current_app.logger.info(f"获取到 {len(tags)} 个标签")
        
        # 获取每个标签的文章数量
        tag_post_counts = {}
        for tag in tags:
            try:
                query = Post.query.filter(
                    Post.tags.any(id=tag.id),
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                tag_post_counts[tag.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取标签 {tag.id} 的文章数量失败: {str(e)}")
                tag_post_counts[tag.id] = 0
        
        # 获取最新评论
        recent_comments = Comment.query.filter_by(status=CommentStatus.APPROVED).order_by(Comment.created_at.desc()).limit(5).all()
        
        # 获取侧边栏数据
        categories = category_service.get_all_categories()
        tags = tag_service.get_all_tags()
        recent_posts = Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(Post.created_at.desc()).limit(5).all()
        
        # 调试日志
        current_app.logger.info(f"获取到的最新文章数量: {len(recent_posts) if recent_posts else 0}")
        if recent_posts:
            for post in recent_posts:
                current_app.logger.info(f"最新文章: ID={post.id}, 标题={post.title}, 状态={post.status}")
        
        # 使用模板渲染
        return render_template('blog/index.html',
                            title="首页",
                            posts=posts,
                            pagination=pagination,
                            archives=archives,
                            categories=categories,
                            category_post_counts=category_post_counts,
                            tags=tags,
                            tag_post_counts=tag_post_counts,
                            sticky_posts=sticky_posts,
                            comment_service=comment_service,
                            recent_comments=recent_comments,
                            recent_posts=recent_posts)
    except Exception as e:
        current_app.logger.error(f"访问首页失败: {str(e)}")
        import traceback
        error_details = traceback.format_exc()
        current_app.logger.error(f"错误详情: {error_details}")
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/post/<int:post_id>', methods=['GET'])
def post_detail(post_id):
    """文章详情页"""
    try:
        # 导入相关模块
        import traceback
        from app.models.comment import CommentStatus
        from app.models.post import PostStatus
        from app.models.comment import Comment
        
        # 获取文章
        post = db.session.get(Post, post_id)
        if not post:
            current_app.logger.error(f"文章不存在: {post_id}")
            abort(404)

        # 增加浏览量
        post.view_count += 1
        db.session.commit()

        # 获取评论列表
        try:
            comments = comment_service.get_post_comments(post_id)
        except Exception as e:
            current_app.logger.error(f"获取评论列表失败: {str(e)}")
            comments = []

        # 获取上一篇和下一篇文章
        try:
            prev_post = post_service.get_prev_post(post)
            next_post = post_service.get_next_post(post)
        except Exception as e:
            current_app.logger.error(f"获取上下篇文章失败: {str(e)}")
            prev_post = next_post = None

        # 获取相关文章
        try:
            related_posts = post_service.get_related_posts(post)
        except Exception as e:
            current_app.logger.error(f"获取相关文章失败: {str(e)}")
            related_posts = []

        # 获取分类和标签
        try:
            categories = category_service.get_all_categories()
            tags = tag_service.get_all_tags()
        except Exception as e:
            current_app.logger.error(f"获取分类和标签失败: {str(e)}")
            categories = []
            tags = []

        # 获取最新文章
        try:
            recent_posts = Post.query.filter(
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
            ).order_by(Post.created_at.desc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"获取最新文章失败: {str(e)}")
            recent_posts = []
        
        # 获取最新评论
        try:
            recent_comments = Comment.query.filter_by(status=CommentStatus.APPROVED).order_by(Comment.created_at.desc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"获取最新评论失败: {str(e)}")
            recent_comments = []

        # 获取每个分类的文章数量
        category_post_counts = {}
        for category in categories:
            try:
                query = Post.query.filter(
                    Post.category_id == category.id,
                    Post.status == PostStatus.PUBLISHED
                )
                category_post_counts[category.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取分类 {category.id} 的文章数量失败: {str(e)}")
                category_post_counts[category.id] = 0

        # 获取每个标签的文章数量
        tag_post_counts = {}
        for tag in tags:
            try:
                query = Post.query.filter(
                    Post.tags.any(id=tag.id),
                    Post.status == PostStatus.PUBLISHED
                )
                tag_post_counts[tag.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取标签 {tag.id} 的文章数量失败: {str(e)}")
                tag_post_counts[tag.id] = 0

        # 准备页面数据
        page_data = {
            'post': post,
            'comments': comments,
            'prev_post': prev_post,
            'next_post': next_post,
            'related_posts': related_posts,
            'categories': categories,
            'category_post_counts': category_post_counts,
            'tags': tags,
            'tag_post_counts': tag_post_counts,
            'recent_posts': recent_posts,
            'recent_comments': recent_comments,
            'current_user': {
                'is_authenticated': current_user.is_authenticated,
                'id': current_user.id if current_user.is_authenticated else None,
                'username': current_user.username if current_user.is_authenticated else None
            },
            'allow_comments': True,  # 启用评论功能
            'version_info': {  # 添加版本信息用于调试
                'content_length': len(post.content) if post.content else 0,
                'html_length': len(post.html_content) if post.html_content else 0,
                'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else None,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }

        return render_template('blog/post_detail.html', **page_data)
    except Exception as e:
        current_app.logger.error(f"获取文章详情失败: {str(e)}")
        traceback.print_exc()  # 打印完整的堆栈信息
        flash('获取文章详情失败', 'error')
        return render_template('blog/error.html', error_message='获取文章详情失败'), 500

@blog_bp.route('/post/<int:post_id>/comment', methods=['POST'])
def create_comment(post_id):
    """创建评论"""
    try:
        # 日志开始处理评论请求
        current_app.logger.info(f"========== 开始处理评论提交请求 ==========")
        current_app.logger.info(f"POST请求到达: post_id={post_id}, content-type={request.content_type}")
        
        if not request.is_json:
            current_app.logger.error("请求不是JSON格式")
            return jsonify({
                'success': False,
                'message': '请求格式错误，请使用JSON格式'
            }), 400
        
        # 处理AJAX/JSON请求
        current_app.logger.info("处理JSON格式评论数据")
        data = request.get_json()
        current_app.logger.info(f"收到JSON数据: {data}")
        
        if not data:
            current_app.logger.warning("未收到有效的JSON数据")
            return jsonify({
                'success': False,
                'message': '无效的请求数据'
            }), 400
            
        content = data.get('content')
        nickname = data.get('nickname')
        email = data.get('email')
        parent_id = data.get('parent_id')
        author_id = data.get('author_id')  # 从JSON数据中获取author_id
        
        current_app.logger.info(f"处理的数据: nickname={nickname}, email={email}, content={content}, parent_id={parent_id}, author_id={author_id}")
            
        # 验证评论内容
        if not content or not content.strip():
            current_app.logger.warning("评论内容为空")
            return jsonify({
                'success': False,
                'message': '评论内容不能为空'
            }), 400
        
        current_app.logger.info(f"评论内容: {content[:30]}... (长度: {len(content)})")
        
        # 获取当前用户 - 如果前端已提供author_id，则优先使用
        if not author_id and current_user.is_authenticated:
            author_id = current_user.id
        
        current_app.logger.info(f"最终使用的作者ID: {author_id}")
        
        # 创建评论
        current_app.logger.info(f"开始创建评论: author_id={author_id}, nickname={nickname}")
        
        # 检查异常情况：匿名用户且未提供昵称
        if not author_id and not nickname:
            current_app.logger.warning("未登录用户且未提供昵称")
            return jsonify({
                'success': False,
                'message': '请提供昵称'
            }), 400
        
        # 使用try/except包裹服务调用，以捕获任何可能的错误
        try:
            result = comment_service.create_comment(
                post_id=post_id,
                content=content,
                author_id=author_id,
                nickname=nickname,
                email=email,
                parent_id=parent_id
            )
            
            current_app.logger.info(f"评论服务返回结果: {result}")
            
            if result['success']:
                current_app.logger.info(f"评论创建成功")
                return jsonify({
                    'success': True,
                    'message': '评论创建成功',
                    'comment': result.get('comment', {})
                })
            else:
                current_app.logger.warning(f"评论创建失败: {result.get('message', '未知错误')}")
                return jsonify({
                    'success': False,
                    'message': result.get('message', '评论创建失败')
                }), 400
                
        except Exception as service_error:
            current_app.logger.error(f"调用评论服务时出错: {str(service_error)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'message': f'评论服务错误: {str(service_error)}'
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"创建评论失败: {str(e)}")
        import traceback
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': '评论创建失败'
        }), 500

@blog_bp.route('/category/<int:category_id>')
def category_posts(category_id):
    """分类页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 获取分类下的文章 - 使用category_service而不是post_service
        pagination = category_service.get_posts_by_category(category_id, page, per_page)
        posts = pagination.items
        
        # 获取分类信息
        category = category_service.get_category_by_id(category_id)
        if not category:
            abort(404)
        
        # 获取所有分类和标签用于侧边栏显示
        categories = category_service.get_all_categories()
        tags = tag_service.get_all_tags()
        
        # 日志记录
        current_app.logger.info(f"获取分类 '{category.name}' (ID: {category_id}) 的文章，共 {pagination.total} 篇")
        
        return render_template('blog/category_posts.html',
                            category=category,
                            posts=posts,
                            pagination=pagination,
                            title=f'分类: {category.name}',
                            categories=categories,
                            tags=tags)
    except Exception as e:
        current_app.logger.error(f"获取分类页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/tag/<int:tag_id>')
def tag_posts(tag_id):
    """标签页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        # 获取标签信息
        tag = tag_service.get_tag_by_id(tag_id)
        if not tag:
            abort(404)
        
        # 直接使用SQLAlchemy查询标签下的文章，而不使用get_posts_by_tag方法
        query = Post.query.filter(
            Post.tags.any(id=tag_id),
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(Post.created_at.desc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        posts = pagination.items
        
        # 获取所有分类和标签用于侧边栏显示
        categories = category_service.get_all_categories()
        tags = tag_service.get_all_tags()
        
        # 日志记录
        current_app.logger.info(f"获取标签 '{tag.name}' (ID: {tag_id}) 的文章，共 {pagination.total} 篇")
        
        return render_template('blog/tag_posts.html',
                            tag=tag,
                            posts=posts,
                            pagination=pagination,
                            title=f'标签: {tag.name}',
                            categories=categories,
                            tags=tags)
    except Exception as e:
        current_app.logger.error(f"获取标签页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/search')
def search():
    """搜索页面"""
    try:
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
    except Exception as e:
        current_app.logger.error(f"搜索失败: {str(e)}")
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/about')
def about():
    """关于页面"""
    try:
        # 准备关于页面的数据
        about = {
            'blog_name': current_app.config.get('BLOG_NAME', 'MyBlog'),
            'blog_description': current_app.config.get('BLOG_DESCRIPTION', '这是一个基于Flask的个人博客系统'),
            'author': current_app.config.get('BLOG_AUTHOR', 'Admin'),
            'created_at': current_app.config.get('BLOG_CREATED_AT', '2024'),
            'github': current_app.config.get('GITHUB_URL', 'https://github.com'),
            'email': current_app.config.get('CONTACT_EMAIL', 'admin@example.com'),
            # 统计数据 - 使用安全的计数方式
            'post_count': Post.query.filter(
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
            ).count(),
            'category_count': Category.query.count(),
            'tag_count': Tag.query.count(),
            'comment_count': Comment.query.filter_by(status=CommentStatus.APPROVED).count(),
            # 当前年份
            'current_year': datetime.now().year
        }
        
        # 获取侧边栏数据
        categories = category_service.get_all_categories()
        tags = tag_service.get_all_tags()
        recent_posts = Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(Post.created_at.desc()).limit(5).all()
        
        # 调试日志
        current_app.logger.info(f"获取到的最新文章数量: {len(recent_posts) if recent_posts else 0}")
        if recent_posts:
            for post in recent_posts:
                current_app.logger.info(f"最新文章: ID={post.id}, 标题={post.title}, 状态={post.status}")
        
        # 获取每个分类的文章数量
        category_post_counts = {}
        for category in categories:
            try:
                query = Post.query.filter(
                    Post.category_id == category.id,
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                category_post_counts[category.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取分类 {category.id} 的文章数量失败: {str(e)}")
                category_post_counts[category.id] = 0
        
        # 获取每个标签的文章数量
        tag_post_counts = {}
        for tag in tags:
            try:
                query = Post.query.filter(
                    Post.tags.any(id=tag.id),
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                tag_post_counts[tag.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取标签 {tag.id} 的文章数量失败: {str(e)}")
                tag_post_counts[tag.id] = 0
        
        return render_template('blog/about.html', 
                            about=about,
                            title='关于',
                            categories=categories,
                            category_post_counts=category_post_counts,
                            tags=tags,
                            tag_post_counts=tag_post_counts,
                            recent_posts=recent_posts)
    except Exception as e:
        current_app.logger.error(f"加载关于页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/categories')
def categories():
    """分类列表页面"""
    try:
        categories = category_service.get_categories_with_post_count()
        return render_template('blog/categories.html', categories=categories)
    except Exception as e:
        current_app.logger.error(f"获取分类列表失败: {str(e)}")
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/tags')
def tags():
    """标签列表页面"""
    try:
        tags = tag_service.get_all_tags()
        return render_template('blog/tags.html', tags=tags)
    except Exception as e:
        current_app.logger.error(f"获取标签列表失败: {str(e)}")
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/archive')
@blog_bp.route('/archive/<date>')
def archive(date=None):
    """
    文章归档页面，全新实现确保正确显示所有文章
    :param date: 归档日期，格式为 yyyy-MM
    :return:
    """
    try:
        # 使用SQLAlchemy ORM直接获取所有文章
        from app.models.post import Post
        
        current_app.logger.info("开始处理归档页面请求...")
        
        # 直接获取所有文章无论状态
        all_posts = Post.query.order_by(Post.created_at.desc()).all()
        
        current_app.logger.info(f"归档页面查询到 {len(all_posts)} 篇文章")
        for post in all_posts:
            current_app.logger.info(f"文章ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
        
        # 按年月分组归档
        archives = {}
        for post in all_posts:
            if not post.created_at:
                continue
            key = f"{post.created_at.year}-{post.created_at.month:02d}"
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
        
        # 创建归档字典，按年月组织
        archive_dict = {}
        sorted_years = []
        
        # 遍历所有归档信息
        for key, posts in archives.items():
            # 分割年月
            year, month = key.split('-')
            year = int(year)
            month = int(month)
            
            # 添加到归档字典
            if year not in archive_dict:
                archive_dict[year] = {}
                sorted_years.append(year)
            
            archive_dict[year][month] = posts
            current_app.logger.info(f"{year}年{month}月: {len(posts)}篇文章")
        
        # 对年份进行排序（降序）
        sorted_years.sort(reverse=True)
        
        # 获取侧边栏数据
        categories = category_service.get_all_categories()
        tags = tag_service.get_all_tags()
        recent_posts = Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(Post.created_at.desc()).limit(5).all()
        
        # 调试日志
        current_app.logger.info(f"获取到的最新文章数量: {len(recent_posts) if recent_posts else 0}")
        if recent_posts:
            for post in recent_posts:
                current_app.logger.info(f"最新文章: ID={post.id}, 标题={post.title}, 状态={post.status}")
        
        # 获取每个分类的文章数量
        category_post_counts = {}
        for category in categories:
            try:
                query = Post.query.filter(
                    Post.category_id == category.id,
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                category_post_counts[category.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取分类 {category.id} 的文章数量失败: {str(e)}")
                category_post_counts[category.id] = 0
        
        # 获取每个标签的文章数量
        tag_post_counts = {}
        for tag in tags:
            try:
                query = Post.query.filter(
                    Post.tags.any(id=tag.id),
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
                )
                tag_post_counts[tag.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取标签 {tag.id} 的文章数量失败: {str(e)}")
                tag_post_counts[tag.id] = 0
        
        return render_template('blog/archive.html',
                            archive_dict=archive_dict,
                            sorted_years=sorted_years,
                            categories=categories,
                            category_post_counts=category_post_counts,
                            tags=tags,
                            tag_post_counts=tag_post_counts,
                            recent_posts=recent_posts)
                            
    except Exception as e:
        current_app.logger.error(f"获取归档页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/login', methods=['GET', 'POST'])
def login():
    """简化的博客前台登录视图"""
    try:
        # 如果用户已经登录，直接跳转到首页
        if current_user.is_authenticated:
            return redirect(url_for('blog.index'))
        
        # 处理POST请求
        if request.method == 'POST':
            # 获取表单数据
            username = request.form.get('username', '')
            password = request.form.get('password', '')
            remember = request.form.get('remember_me') == 'y'
            
            # 查询用户
            from app.models.user import User
            user = User.query.filter_by(username=username).first()
            
            # 验证密码
            if user and user.verify_password(password):
                # 移除管理员限制检查，允许任何用户登录前台
                login_user(user, remember=remember)
                flash('登录成功', 'success')
                return redirect(url_for('blog.index'))
            else:
                flash('用户名或密码错误', 'danger')
        
        # 返回登录页面
        return render_template('blog/login.html')
    except Exception as e:
        current_app.logger.error(f"登录失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        flash('登录失败，请稍后再试', 'danger')
        return render_template('blog/login.html')

@blog_bp.route('/logout')
@login_required
def logout():
    """博客前台退出"""
    try:
        logout_user()
        flash('您已退出登录', 'success')
        return redirect(url_for('blog.index'))
    except Exception as e:
        current_app.logger.error(f"用户退出失败: {str(e)}")
        flash('退出失败，请稍后再试', 'error')
        return redirect(url_for('blog.index'))

@blog_bp.route('/archive_test')
def archive_test():
    """
    测试归档页面，直接使用SQL获取文章
    """
    try:
        from app.extensions import db
        from sqlalchemy import text
        from app.models.post import Post
        
        # 直接使用原生SQL查询获取所有文章，包括归档状态
        sql = text("""
            SELECT id, title, content, created_at, category_id, status
            FROM posts 
            ORDER BY created_at DESC
        """)
        
        result = db.session.execute(sql)
        posts_data = []
        
        for row in result:
            posts_data.append({
                'id': row.id,
                'title': row.title, 
                'status': row.status,
                'created_at': row.created_at
            })
        
        # 返回结果
        from flask import jsonify
        return jsonify({
            'total_posts': len(posts_data),
            'posts': posts_data
        })
                            
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"获取归档测试页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return {'error': str(e)}, 500

@blog_bp.route('/archive_sql')
def archive_sql():
    """
    使用直接SQL查询的归档页面
    """
    try:
        import sqlite3
        from datetime import datetime
        
        # 连接SQLite数据库
        db_path = '/data/myblog/instance/blog-dev.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有已发布和已归档的文章
        cursor.execute("""
            SELECT p.id, p.title, p.created_at, c.id as category_id, c.name as category_name
            FROM posts p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.status = 'PUBLISHED' OR p.status = 'ARCHIVED'
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        current_app.logger.info(f"直接SQL查询到 {len(rows)} 篇文章")
        
        # 打印文章状态
        cursor.execute("SELECT status, COUNT(*) as count FROM posts GROUP BY status")
        status_counts = cursor.fetchall()
        for status in status_counts:
            current_app.logger.info(f"状态: {status['status']}, 数量: {status['count']}")
        
        # 创建文章对象列表
        all_posts = []
        for row in rows:
            # 创建一个简单的类来存储文章数据
            class PostObj:
                pass
            
            post = PostObj()
            post.id = row['id']
            post.title = row['title']
            
            # 处理创建时间
            created_at = row['created_at']
            if isinstance(created_at, str):
                try:
                    post.created_at = datetime.fromisoformat(created_at)
                except:
                    post.created_at = datetime.now()  # 默认值
            else:
                post.created_at = created_at
            
            # 处理分类
            if row['category_id']:
                class CategoryObj:
                    pass
                
                category = CategoryObj()
                category.id = row['category_id']
                category.name = row['category_name']
                post.category = category
            else:
                post.category = None
            
            all_posts.append(post)
            current_app.logger.info(f"添加文章: ID={post.id}, 标题={post.title}, 创建时间={post.created_at}")
        
        # 按年月分组归档
        archives = {}
        for post in all_posts:
            if not post.created_at:
                continue
            key = f"{post.created_at.year}-{post.created_at.month:02d}"
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
        
        # 创建归档字典，按年月组织
        archive_dict = {}
        sorted_years = []
        
        # 遍历所有归档信息
        for key, posts in archives.items():
            # 分割年月
            year, month = key.split('-')
            year = int(year)
            month = int(month)
            
            # 添加到归档字典
            if year not in archive_dict:
                archive_dict[year] = {}
                sorted_years.append(year)
            
            archive_dict[year][month] = posts
            current_app.logger.info(f"{year}年{month}月: {len(posts)}篇文章")
        
        # 对年份进行排序（降序）
        sorted_years.sort(reverse=True)
        
        # 关闭数据库连接
        conn.close()
        
        return render_template('blog/archive.html',
                              archive_dict=archive_dict,
                              sorted_years=sorted_years)
        
    except Exception as e:
        current_app.logger.error(f"SQL归档页面出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/all_archives')
def all_archives():
    """
    全新实现的归档页面，确保显示所有状态的文章
    """
    try:
        import sqlite3
        from datetime import datetime
        
        # 连接SQLite数据库
        db_path = '/data/myblog/instance/blog-dev.db'
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 输出所有文章状态以便调试
        cursor.execute("SELECT DISTINCT status FROM posts")
        statuses = [row['status'] for row in cursor.fetchall()]
        current_app.logger.info(f"数据库中的文章状态: {statuses}")
        
        # 查询所有文章(无论状态)，为了调试目的
        cursor.execute("""
            SELECT p.id, p.title, p.created_at, p.status, c.id as category_id, c.name as category_name
            FROM posts p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.created_at DESC
        """)
        
        rows = cursor.fetchall()
        current_app.logger.info(f"所有文章查询结果: {len(rows)} 篇")
        
        # 创建文章对象列表
        all_posts = []
        for row in rows:
            # 创建一个简单的类来存储文章数据
            class PostObj:
                pass
            
            post = PostObj()
            post.id = row['id']
            post.title = row['title']
            post.status = row['status']
            
            # 记录每篇文章的状态便于调试
            current_app.logger.info(f"文章ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
            
            # 处理创建时间
            created_at = row['created_at']
            if isinstance(created_at, str):
                try:
                    post.created_at = datetime.fromisoformat(created_at)
                except:
                    post.created_at = datetime.now()  # 默认值
            else:
                post.created_at = created_at
            
            # 处理分类
            if row['category_id']:
                class CategoryObj:
                    pass
                
                category = CategoryObj()
                category.id = row['category_id']
                category.name = row['category_name']
                post.category = category
            else:
                post.category = None
            
            # 添加所有文章到列表
            all_posts.append(post)
        
        # 按年月分组归档
        archives = {}
        for post in all_posts:
            if not post.created_at:
                continue
            key = f"{post.created_at.year}-{post.created_at.month:02d}"
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
        
        # 创建归档字典，按年月组织
        archive_dict = {}
        sorted_years = []
        
        # 遍历所有归档信息
        for key, posts in archives.items():
            # 分割年月
            year, month = key.split('-')
            year = int(year)
            month = int(month)
            
            # 添加到归档字典
            if year not in archive_dict:
                archive_dict[year] = {}
                sorted_years.append(year)
            
            archive_dict[year][month] = posts
            current_app.logger.info(f"{year}年{month}月: {len(posts)}篇文章")
        
        # 对年份进行排序（降序）
        sorted_years.sort(reverse=True)
        
        # 关闭数据库连接
        conn.close()
        
        return render_template('blog/archive.html',
                              archive_dict=archive_dict,
                              sorted_years=sorted_years)
        
    except Exception as e:
        current_app.logger.error(f"获取所有归档页面失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return render_template('blog/error.html', error_message='服务器内部错误'), 500

@blog_bp.route('/direct_archive')
def direct_archive():
    """直接从数据库读取并显示归档页面"""
    try:
        import sqlite3
        from datetime import datetime
        from flask import current_app, render_template
        
        # 连接数据库
        db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 查询所有已发布和已归档的文章
        cursor.execute("""
            SELECT id, title, created_at, status 
            FROM posts 
            WHERE status IN ('PUBLISHED', 'ARCHIVED', 'published', 'archived')
            ORDER BY created_at DESC
        """)
        all_posts = cursor.fetchall()
        
        # 为调试输出文章数量和状态
        print(f"获取到 {len(all_posts)} 篇文章")
        for post in all_posts:
            print(f"文章ID: {post['id']}, 标题: {post['title']}, 状态: {post['status']}")
        
        # 按年月分组
        archive_dict = {}
        for post in all_posts:
            created_at = post['created_at']
            if isinstance(created_at, str):
                # 转换字符串日期为datetime对象
                try:
                    dt = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        dt = datetime.strptime(created_at, '%Y-%m-%d')
                    except ValueError:
                        # 如果无法解析，使用当前日期
                        dt = datetime.now()
            else:
                # 如果是数字(时间戳)，转换为datetime
                try:
                    dt = datetime.fromtimestamp(created_at)
                except (TypeError, ValueError):
                    dt = datetime.now()
            
            year = dt.year
            month = dt.month
            
            if year not in archive_dict:
                archive_dict[year] = {}
            
            if month not in archive_dict[year]:
                archive_dict[year][month] = []
            
            archive_dict[year][month].append({
                'id': post['id'],
                'title': post['title'],
                'status': post['status']
            })
        
        # 关闭连接
        conn.close()
        
        # 返回HTML
        result = '<h1>文章归档</h1>'
        
        # 添加调试信息
        result += f'<p>共找到 {len(all_posts)} 篇文章</p>'
        
        # 按年月排序
        for year in sorted(archive_dict.keys(), reverse=True):
            result += f'<h2>{year}年</h2>'
            for month in sorted(archive_dict[year].keys(), reverse=True):
                result += f'<h3>{month}月</h3><ul>'
                for post in archive_dict[year][month]:
                    status_mark = ' [归档]' if post['status'].upper() == 'ARCHIVED' else ''
                    result += f'<li><a href="/blog/post/{post["id"]}">{post["title"]}</a>{status_mark}</li>'
                result += '</ul>'
        
        return result
    except Exception as e:
        import traceback
        error_message = f"归档页面加载失败: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_message)
        return f'<h1>归档页面加载失败</h1><pre>{error_message}</pre>'

@blog_bp.route('/test_comment', methods=['GET', 'POST'])
def test_comment():
    """测试评论功能"""
    try:
        # 查找一篇已发布的文章
        post = Post.query.filter_by(status=PostStatus.PUBLISHED).first()
        if not post:
            return "没有找到任何已发布文章，无法测试评论功能", 404
        
        if request.method == 'POST':
            # 处理评论提交
            content = request.form.get('content')
            nickname = request.form.get('nickname')
            email = request.form.get('email')
            
            # 验证评论内容
            if not content or not content.strip():
                flash('评论内容不能为空', 'error')
                return redirect(url_for('blog.test_comment'))
            
            # 获取当前用户
            user = current_user if current_user.is_authenticated else None
            
            if not user and not nickname:
                flash('请提供昵称', 'error')
                return redirect(url_for('blog.test_comment'))
            
            # 创建评论
            result = comment_service.create_comment(
                post_id=post.id,
                content=content,
                author_id=user.id if user else None,
                nickname=nickname,
                email=email
            )
            
            if result['success']:
                flash('评论提交成功, 已自动通过审核', 'success')
            else:
                flash(result['message'], 'error')
            
            return redirect(url_for('blog.test_comment'))
        
        # 获取评论列表
        comments = comment_service.get_post_comments(post.id)
        
        # 准备页面数据
        return render_template('blog/test_comment.html', 
                            post=post,
                            comments=comments,
                            current_user=current_user)
    except Exception as e:
        current_app.logger.error(f"测试评论功能失败: {str(e)}")
        import traceback
        current_app.logger.error(f"错误详情: {traceback.format_exc()}")
        return str(e), 500

@blog_bp.route('/test_post/<int:post_id>', methods=['GET'])
def test_post_detail(post_id):
    """测试文章详情页，使用新的模板"""
    try:
        # 导入相关模块
        import traceback
        from app.models.comment import CommentStatus
        from app.models.post import PostStatus
        from app.models.comment import Comment
        
        # 记录日志开始
        current_app.logger.info(f"========== 访问测试文章详情页 ==========")
        current_app.logger.info(f"文章ID: {post_id}")
        
        # 获取文章
        post = db.session.get(Post, post_id)
        if not post:
            current_app.logger.error(f"文章不存在: {post_id}")
            abort(404)

        # 增加浏览量
        post.view_count += 1
        db.session.commit()

        # 获取评论列表
        try:
            comments = Comment.query.filter_by(post_id=post_id, status=CommentStatus.APPROVED).all()
            current_app.logger.info(f"获取到 {len(comments)} 条评论")
        except Exception as e:
            current_app.logger.error(f"获取评论列表失败: {str(e)}")
            comments = []

        # 获取上一篇和下一篇文章
        try:
            prev_post = post_service.get_prev_post(post)
            next_post = post_service.get_next_post(post)
        except Exception as e:
            current_app.logger.error(f"获取上下篇文章失败: {str(e)}")
            prev_post = next_post = None

        # 获取相关文章
        try:
            related_posts = post_service.get_related_posts(post)
        except Exception as e:
            current_app.logger.error(f"获取相关文章失败: {str(e)}")
            related_posts = []

        # 获取分类和标签
        try:
            categories = category_service.get_all_categories()
            tags = tag_service.get_all_tags()
        except Exception as e:
            current_app.logger.error(f"获取分类和标签失败: {str(e)}")
            categories = []
            tags = []

        # 获取最新文章
        try:
            recent_posts = Post.query.filter(
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
            ).order_by(Post.created_at.desc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"获取最新文章失败: {str(e)}")
            recent_posts = []
        
        # 获取最新评论
        try:
            recent_comments = Comment.query.filter_by(status=CommentStatus.APPROVED).order_by(Comment.created_at.desc()).limit(5).all()
        except Exception as e:
            current_app.logger.error(f"获取最新评论失败: {str(e)}")
            recent_comments = []

        # 获取每个分类的文章数量
        category_post_counts = {}
        for category in categories:
            try:
                query = Post.query.filter(
                    Post.category_id == category.id,
                    Post.status == PostStatus.PUBLISHED
                )
                category_post_counts[category.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取分类 {category.id} 的文章数量失败: {str(e)}")
                category_post_counts[category.id] = 0

        # 获取每个标签的文章数量
        tag_post_counts = {}
        for tag in tags:
            try:
                query = Post.query.filter(
                    Post.tags.any(id=tag.id),
                    Post.status == PostStatus.PUBLISHED
                )
                tag_post_counts[tag.id] = query.count()
            except Exception as e:
                current_app.logger.error(f"获取标签 {tag.id} 的文章数量失败: {str(e)}")
                tag_post_counts[tag.id] = 0

        # 准备页面数据
        page_data = {
            'post': post,
            'comments': comments,
            'prev_post': prev_post,
            'next_post': next_post,
            'related_posts': related_posts,
            'categories': categories,
            'category_post_counts': category_post_counts,
            'tags': tags,
            'tag_post_counts': tag_post_counts,
            'recent_posts': recent_posts,
            'recent_comments': recent_comments,
            'current_user': {
                'is_authenticated': current_user.is_authenticated,
                'id': current_user.id if current_user.is_authenticated else None,
                'username': current_user.username if current_user.is_authenticated else None
            }
        }

        current_app.logger.info("使用新的测试模板渲染文章详情页")
        return render_template('blog/test_post.html', **page_data)
    except Exception as e:
        current_app.logger.error(f"获取测试文章详情失败: {str(e)}")
        traceback.print_exc()  # 打印完整的堆栈信息
        flash('获取文章详情失败', 'error')
        return render_template('blog/error.html', error_message='获取文章详情失败'), 500

@blog_bp.route('/post/<int:post_id>/direct_comment', methods=['GET', 'POST'])
def direct_comment(post_id):
    """直接评论页面"""
    try:
        # 导入相关模块
        import traceback
        from app.models.comment import CommentStatus
        from app.models.post import PostStatus
        from app.models.comment import Comment
        
        # 获取文章
        post = db.session.get(Post, post_id)
        if not post:
            current_app.logger.error(f"文章不存在: {post_id}")
            abort(404)
        
        # 获取评论列表
        comments = comment_service.get_post_comments(post_id)
        current_app.logger.info(f"获取到文章 {post_id} 的评论数量: {len(comments)}")
        
        if request.method == 'POST':
            # 处理评论提交
            content = request.form.get('content')
            nickname = request.form.get('nickname')
            email = request.form.get('email')
            
            # 验证评论内容
            if not content or not content.strip():
                flash('评论内容不能为空', 'error')
                return redirect(url_for('blog.direct_comment', post_id=post_id))
            
            # 获取当前用户
            user = current_user if current_user.is_authenticated else None
            
            if not user and not nickname:
                flash('请提供昵称', 'error')
                return redirect(url_for('blog.direct_comment', post_id=post_id))
            
            # 创建评论
            result = comment_service.create_comment(
                post_id=post_id,
                content=content,
                author_id=user.id if user else None,
                nickname=nickname,
                email=email
            )
            
            if result['success']:
                flash('评论提交成功, 已自动通过审核', 'success')
            else:
                flash(result['message'], 'error')
            
            return redirect(url_for('blog.direct_comment', post_id=post_id))
        
        return render_template('blog/direct_comment.html', 
                           post=post,
                           comments=comments,
                           current_user=current_user)
    except Exception as e:
        current_app.logger.error(f"直接评论页面失败: {str(e)}")
        traceback.print_exc()
        flash('获取评论页面失败', 'error')
        return render_template('blog/error.html', error_message='获取评论页面失败'), 500

@blog_bp.route('/simple_post/<int:post_id>', methods=['GET'])
def simple_post_detail(post_id):
    """简化版文章详情页，用于排查问题"""
    try:
        # 记录日志
        current_app.logger.info(f"访问简化版文章详情页: ID={post_id}")
        
        # 获取文章
        post = db.session.get(Post, post_id)
        if not post:
            current_app.logger.error(f"文章不存在: {post_id}")
            abort(404)
            
        # 增加浏览量
        post.view_count += 1
        db.session.commit()
        
        # 获取最近文章
        recent_posts = Post.query.filter_by(status=PostStatus.PUBLISHED).order_by(Post.created_at.desc()).limit(5).all()
        
        # 准备页面数据
        page_data = {
            'post': post,
            'recent_posts': recent_posts,
        }
        
        # 渲染简化模板
        return render_template('blog/simple_post.html', **page_data)
    except Exception as e:
        current_app.logger.error(f"简化版文章详情页出错: {str(e)}")
        traceback.print_exc()
        return render_template('blog/error.html', error_message=f"加载文章失败: {str(e)}"), 500

@blog_bp.route('/direct_post/<int:post_id>')
def direct_post(post_id):
    """直接以纯文本输出文章内容，避免模板渲染问题"""
    try:
        # 查询文章
        post = db.session.get(Post, post_id)
        if not post:
            return f"文章不存在：ID={post_id}", 404
        
        # 增加浏览量
        post.view_count += 1
        db.session.commit()
        
        # 准备输出内容
        output = []
        output.append(f"文章ID: {post.id}")
        output.append(f"标题: {post.title}")
        output.append(f"发布时间: {post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else 'unknown'}")
        output.append(f"更新时间: {post.updated_at.strftime('%Y-%m-%d %H:%M:%S') if post.updated_at else 'unknown'}")
        output.append(f"状态: {post.status}")
        output.append(f"分类: {post.category.name if post.category else 'unknown'}")
        output.append(f"浏览量: {post.view_count}")
        
        # 添加标签信息
        tags = [tag.name for tag in post.tags] if post.tags else []
        output.append(f"标签: {', '.join(tags) if tags else 'none'}")
        
        # 添加正文内容
        output.append("\n--- 正文开始 ---")
        output.append(post.content or "")
        output.append("--- 正文结束 ---")
        
        # 以纯文本形式返回
        response = make_response("\n".join(output))
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        return response
    except Exception as e:
        import traceback
        error_details = f"获取文章失败：{str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_details)
        return error_details, 500

@blog_bp.route('/minimal_post/<int:post_id>')
def minimal_post(post_id):
    """最小化实现的文章详情页，仅使用必要的数据库操作"""
    try:
        # 直接查询文章
        post = db.session.get(Post, post_id)
        if not post:
            return f"文章不存在：ID={post_id}", 404
        
        # 增加浏览量
        post.view_count += 1
        db.session.commit()
        
        # 构建HTML响应，不使用模板
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{post.title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .header {{ border-bottom: 1px solid #eee; padding-bottom: 10px; margin-bottom: 20px; }}
                .content {{ line-height: 1.6; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{post.title}</h1>
                    <p>发布时间：{post.created_at.strftime('%Y-%m-%d %H:%M:%S') if post.created_at else '未知'}</p>
                    <p>浏览次数：{post.view_count}</p>
                </div>
                <div class="content">
                    {post.html_content or post.content or '无内容'}
                </div>
                <div class="footer">
                    <p><a href="/">返回首页</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
        
    except Exception as e:
        import traceback
        error_msg = f"访问文章出错: {str(e)}\n{traceback.format_exc()}"
        current_app.logger.error(error_msg)
        return error_msg, 500

@blog_bp.route('/register')
def register():
    """博客前台注册视图 - 目前仅做为占位符，防止404错误"""
    flash('目前不支持自助注册，请联系管理员创建账号', 'warning')
    return redirect(url_for('blog.login'))

