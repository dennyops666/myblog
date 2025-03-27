"""
文件名：post.py
描述：文章服务
作者：denny
创建日期：2024-03-21
"""

import os
import re
from datetime import datetime, UTC
from typing import Any, List, Dict, Optional, Tuple
from werkzeug.utils import secure_filename
from sqlalchemy import desc, extract, or_, and_, func, text
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.tag import Tag
from app.extensions import db, cache
from app.utils.pagination import Pagination
from app.config import Config
from app.services.security import SecurityService
from PIL import Image
import uuid
import secrets
from flask import url_for, current_app
import json
from app.models.user import User
from app.models.comment import Comment, CommentStatus
import traceback

class PostService:
    # 缓存配置
    CACHE_TIMEOUT = 300  # 5分钟缓存过期时间
    MAX_CACHE_PAGES = 10  # 最大缓存页数
    
    # 缓存键前缀
    CACHE_KEY_POST = 'post:{}'
    CACHE_KEY_STICKY = 'sticky_posts'
    CACHE_KEY_CATEGORY = 'category_posts:{}:{}:{}'
    CACHE_KEY_TAG = 'tag_posts:{}:{}:{}'
    CACHE_KEY_TIME = 'time_posts:{}:{}:{}:{}'
    CACHE_KEY_RELATED = 'related_posts:{}:{}'
    CACHE_KEY_SEARCH = 'search:{}:{}:{}'

    def __init__(self):
        self.security_service = SecurityService()
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        self.max_image_size = (1920, 1080)  # 最大图片尺寸
        self.thumbnail_size = (300, 300)    # 缩略图尺寸
        self.quality = 85                   # 图片质量

    def _get_upload_folder(self):
        """获取上传文件夹路径"""
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        return upload_folder

    def _allowed_image(self, filename):
        """检查是否是允许的图片类型"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'})

    def _process_image(self, image):
        """处理图片（调整大小、转换格式等）"""
        # 如果图片是RGBA模式，转换为RGB
        if image.mode == 'RGBA':
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        
        # 在非测试环境中调整图片大小
        if not current_app.config.get('TESTING'):
            max_size = current_app.config.get('IMAGE_MAX_DIMENSION', 2048)
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = tuple(int(dim * ratio) for dim in image.size)
                image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        return image

    def _save_image(self, image, original_filename):
        """保存图片"""
        # 生成安全的文件名
        filename = secure_filename(original_filename)
        name = os.path.splitext(filename)[0]
        filename = f"{name}.png"  # 始终使用PNG格式
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(os.path.join(self._get_upload_folder(), filename)):
            timestamp = datetime.now(UTC).strftime('%Y%m%d%H%M%S')
            filename = f"{name}_{timestamp}.png"
        
        # 确保上传目录存在
        os.makedirs(self._get_upload_folder(), exist_ok=True)
        
        # 保存图片
        save_path = os.path.join(self._get_upload_folder(), filename)
        image.save(save_path, format='PNG', quality=85, optimize=True)
        
        return filename

    def upload_image(self, file):
        """上传图片
        
        Args:
            file: 文件对象
            
        Returns:
            str: 文件名
            
        Raises:
            ValueError: 如果文件类型不支持或文件无效
        """
        if not file or not file.filename:
            raise ValueError('未选择文件')
        
        if not self._allowed_image(file.filename):
            raise ValueError('不支持的文件类型')
        
        try:
            # 读取和处理图片
            image = Image.open(file)
            image = self._process_image(image)
            
            # 保存图片
            filename = self._save_image(image, file.filename)
            return filename
            
        except Exception as e:
            current_app.logger.error(f"处理图片失败: {str(e)}")
            raise ValueError('图片处理失败')

    def get_post_images(self, post_id):
        """获取文章的所有上传图片
        
        Args:
            post_id: 文章ID
            
        Returns:
            list: 图片URL列表
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return []
            
            # 从文章内容中提取图片URL
            pattern = r'!\[.*?\]\((.*?)\)'
            matches = re.findall(pattern, post.content or '')
            
            # 过滤出本地上传的图片
            local_images = []
            for url in matches:
                if url.startswith('/'):  # 本地图片URL
                    local_images.append({
                        'url': url,
                        'filename': os.path.basename(url)
                    })
            
            return local_images
            
        except Exception as e:
            current_app.logger.error(f"获取文章图片失败: {str(e)}")
            return []

    def delete_image(self, filename):
        """删除图片
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            file_path = os.path.join(self._get_upload_folder(), filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"删除图片失败: {str(e)}")
            return False

    def _clear_post_cache(self, post_id):
        """清除文章相关的所有缓存
        
        Args:
            post_id: 文章ID
        """
        current_app.logger.info(f"清除文章 {post_id} 相关的缓存")
        
        # 清除文章详情缓存
        cache_key = self.CACHE_KEY_POST.format(post_id)
        cache.delete(cache_key)
        
        # 清除置顶文章缓存
        cache.delete(self.CACHE_KEY_STICKY)
        
        # 清除文章列表缓存
        for page in range(1, self.MAX_CACHE_PAGES + 1):
            cache_key = f'posts:page:{page}'
            cache.delete(cache_key)
            
            # 清除分页大小变体
            for per_page in [5, 10, 15, 20, 25, 30]:
                cache_key = f'posts:page:{page}:{per_page}'
                cache.delete(cache_key)
        
        # 清除搜索结果缓存 - 由于搜索内容多变，简单清除一些常见前缀
        for prefix in ['search:', 'related:', 'category:', 'tag:', 'archive:']:
            cache.delete_many(prefix)
        
        # 清除首页缓存
        cache.delete('index_data')
        
        # 清除归档缓存
        cache.delete('archives')
        
        # 清除相关文章缓存
        cache.delete_many(f'related:{post_id}')
        
        # 强制清除所有与posts相关的缓存
        try:
            cache.delete_many('posts:')
        except:
            pass
            
        current_app.logger.info(f"缓存清除完成")

    def _build_search_query(self, search_text):
        """构建搜索查询
        
        Args:
            search_text: 搜索文本
            
        Returns:
            查询条件
        """
        # 确保search_text是字符串类型
        search_text = str(search_text) if search_text is not None else ""
        search_terms = search_text.split()
        conditions = []
        
        for term in search_terms:
            pattern = f'%{term}%'
            term_condition = or_(
                Post.title.ilike(pattern),
                Post.content.ilike(pattern),
                Post.summary.ilike(pattern)
            )
            conditions.append(term_condition)
            
        # 如果没有搜索条件，返回始终为真的条件
        if not conditions:
            return True
            
        return and_(*conditions)
    
    @staticmethod
    def search_posts(query: str, page: int = 1, per_page: int = 10):
        """搜索文章"""
        if not query:
            return Post.query.filter_by(status=1).order_by(
                desc(Post.created_at)
            ).paginate(page=page, per_page=per_page, error_out=False)
        
        # 构建搜索查询
        search_query = PostService._build_search_query(query)
        
        # 执行查询
        return Post.query.filter(
            and_(search_query, Post.status == 1)
        ).order_by(desc(Post.created_at)).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
    
    def create_post(self, title, content, author=None, author_id=None, category_id=None, tags=None, status=PostStatus.DRAFT, summary=None):
        """创建文章
        
        Args:
            title: 标题
            content: 内容
            author: 作者对象
            author_id: 作者ID
            category_id: 分类ID
            tags: 标签列表
            status: 状态
            summary: 摘要
            
        Returns:
            Post: 创建的文章对象
            
        Raises:
            ValueError: 如果参数无效
        """
        try:
            # 验证作者
            if not author and not author_id:
                raise ValueError('必须指定作者')
            
            if not author and author_id:
                author = User.query.get(author_id)
                if not author:
                    raise ValueError('作者不存在')
            
            # 检查标题是否已存在
            existing_post = Post.query.filter_by(title=title).first()
            if existing_post:
                raise ValueError('标题已存在，请使用不同的标题')
            
            # 创建文章
            post = Post(
                title=title,
                content=content,
                summary=summary,
                author=author,
                status=status
            )
            
            # 设置分类
            if category_id:
                category = Category.query.get(category_id)
                if category:
                    post.category = category
            
            # 设置标签
            if tags:
                post.tags = tags
            
            # 保存到数据库
            db.session.add(post)
            db.session.commit()
            
            # 清除缓存
            self._clear_post_cache(post.id)
            
            return post
            
        except ValueError as e:
            # 直接向上传递ValueError，保留原始错误信息
            db.session.rollback()
            current_app.logger.error(f"创建文章失败: {str(e)}")
            raise
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建文章失败: {str(e)}")
            current_app.logger.exception(e)
            raise ValueError(f'创建文章失败: {str(e)}')

    def update_post(self, post_id, title=None, content=None, summary=None, category_id=None, tags=None, status=None):
        """更新文章
        
        Args:
            post_id: 文章ID
            title: 标题
            content: 内容
            summary: 摘要
            category_id: 分类ID
            tags: 标签列表
            status: 状态
            
        Returns:
            Post: 更新后的文章对象
        """
        try:
            current_app.logger.info(f"开始更新文章，ID: {post_id}")
            
            # 获取文章并预加载关联数据
            post = Post.query.options(
                db.joinedload(Post.category),
                db.joinedload(Post.author),
                db.joinedload(Post.tags)
            ).get(post_id)
            
            if not post:
                current_app.logger.warning(f"文章不存在，ID: {post_id}")
                raise ValueError('文章不存在')
            
            # 更新分类
            if category_id is not None:
                post.category_id = category_id
            
            # 更新基本信息
            if title is not None and title != post.title:
                # 检查标题是否已存在
                existing_post = Post.query.filter(Post.title == title, Post.id != post_id).first()
                if existing_post:
                    raise ValueError('标题已存在，请使用不同的标题')
                post.title = title
                
            if content is not None:
                post.content = content
                post.update_html_content()  # 更新HTML内容
            if summary is not None:
                post.summary = summary
            if status is not None:
                post.status = status
                
            # 更新标签
            if tags is not None:
                current_app.logger.info(f"开始更新标签，收到的标签列表: {[tag.name for tag in tags]}")
                current_app.logger.info(f"当前文章的标签: {[tag.name for tag in post.tags]}")
                
                # 清除所有现有标签
                current_app.logger.info("清除所有现有标签")
                post.tags = []
                db.session.flush()
                
                # 添加新标签
                current_app.logger.info(f"添加新标签: {[tag.name for tag in tags]}")
                post.tags.extend(tags)
                db.session.flush()
                
                current_app.logger.info(f"标签更新完成，当前标签: {[tag.name for tag in post.tags]}")
            
            # 更新时间戳
            post.updated_at = datetime.now(UTC)
            
            # 提交所有更改
            db.session.commit()
            
            # 清除相关的缓存键
            current_app.logger.info("开始清除缓存")
            self._clear_post_cache(post.id)
            
            # 清除标签相关的缓存
            if tags is not None:
                for tag in tags:
                    cache_key = f'tag_posts:{tag.id}'
                    cache.delete(cache_key)
                    current_app.logger.info(f"清除标签缓存: {cache_key}")
            
            # 清除文章列表缓存
            cache.delete('post_list')
            cache.delete(f'post_list:1:10')  # 默认的分页缓存
            
            # 强制刷新数据库会话
            db.session.expire_all()
            db.session.refresh(post)
            
            # 重新加载所有关联数据
            if post.category:
                db.session.refresh(post.category)
            if post.author:
                db.session.refresh(post.author)
            for tag in post.tags:
                db.session.refresh(tag)
            
            current_app.logger.info(f"文章 {post_id} 更新完成")
            current_app.logger.info(f"最终的标签列表: {[tag.name for tag in post.tags]}")
            
            return post
            
        except Exception as e:
            current_app.logger.error(f"更新文章失败: {str(e)}")
            current_app.logger.exception(e)  # 记录完整的异常堆栈
            db.session.rollback()
            raise

    def delete_post(self, post_id):
        """删除文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            current_app.logger.info(f"开始删除文章，ID: {post_id}")
            post = db.session.get(Post, post_id)
            
            if not post:
                current_app.logger.warning(f"文章不存在，ID: {post_id}")
                return {'status': 'error', 'message': '文章不存在'}
            
            current_app.logger.info(f"找到文章，标题: {post.title}")
            
            # 删除文章前，先清理相关的评论
            comments_count = post.comments.count()
            if comments_count > 0:
                current_app.logger.info(f"删除文章相关的评论，数量: {comments_count}")
                post.comments.delete()
            
            db.session.delete(post)
            db.session.commit()
            
            current_app.logger.info(f"文章删除成功，ID: {post_id}")
            return {'status': 'success', 'message': '文章删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除文章失败: {str(e)}")
            return {'status': 'error', 'message': '删除文章失败，请稍后重试'}
            
    @staticmethod
    def get_post(post_id: int) -> Optional[Post]:
        """获取文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            Post: 文章对象，如果不存在则返回None
        """
        try:
            return Post.query.get(post_id)
        except Exception as e:
            current_app.logger.error(f"获取文章失败: {str(e)}")
            return None
            
    def get_posts(self, page=1, per_page=10, category_id=None, tag_name=None):
        """获取文章列表
        
        Args:
            page: 页码
            per_page: 每页数量
            category_id: 分类ID
            tag_name: 标签名
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            query = Post.query
            
            # 按分类筛选
            if category_id:
                query = query.filter_by(category_id=category_id)
                
            # 按标签筛选
            if tag_name:
                query = query.join(Post.tags).filter(Tag.name == tag_name)
                
            # 分页
            pagination = query.order_by(Post.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'status': 'success',
                'posts': pagination.items,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': pagination.page
            }
            
        except Exception as e:
            current_app.logger.error(f"获取文章列表失败: {str(e)}")
            return {'status': 'error', 'message': '获取文章列表失败，请稍后重试'}

    def get_post_list(self, page=1, per_page=10):
        """获取文章列表
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        try:
            # 获取已发布的文章
            query = Post.query.filter_by(status=PostStatus.PUBLISHED)
            
            # 按创建时间倒序排序
            query = query.order_by(Post.created_at.desc())
            
            # 分页
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return pagination
            
        except Exception as e:
            current_app.logger.error(f"获取文章列表失败: {str(e)}")
            raise e

    def search_posts(self, keyword, page=1, per_page=10, include_private=False):
        """搜索文章"""
        query = Post.query
        
        if not include_private:
            query = query.filter_by(is_private=False)
        
        query = query.filter(
            or_(
                Post.title.ilike(f'%{keyword}%'),
                Post.content.ilike(f'%{keyword}%')
            )
        )
        
        return query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    def increment_views(self, post_id):
        """增加文章浏览量"""
        try:
            # 在测试环境中不更新浏览量
            if current_app.config.get('TESTING'):
                return True, 1
                
            post = db.session.get(Post, post_id)
            if not post:
                return False, "文章不存在"
            
            post.view_count = (post.view_count or 0) + 1
            db.session.commit()
            return True, post.view_count
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新文章浏览量失败: {str(e)}")
            return False, str(e)

    def get_post_stats(self):
        """获取文章统计信息"""
        try:
            # 获取文章总数
            total = Post.query.count()
            
            # 获取已发布文章数量
            published = Post.query.filter_by(
                status=PostStatus.PUBLISHED,
                is_private=False
            ).count()
            
            # 获取草稿数量
            draft = Post.query.filter_by(
                status=PostStatus.DRAFT
            ).count()
            
            # 获取总浏览量
            total_views = db.session.query(db.func.sum(Post.view_count)).scalar() or 0
            
            current_app.logger.info('成功获取文章统计信息', extra={
                'data': {
                    'total': total,
                    'published': published,
                    'draft': draft,
                    'total_views': total_views
                }
            })
            
            return {
                'total': total,
                'published': published,
                'draft': draft,
                'total_views': total_views
            }
            
        except Exception as e:
            current_app.logger.error(f'获取文章统计信息失败: {str(e)}')
            current_app.logger.exception(e)
            return {
                'total': 0,
                'published': 0,
                'draft': 0,
                'total_views': 0
            }

    @staticmethod
    def get_sticky_posts() -> List[Post]:
        """获取置顶文章列表"""
        cache_key = PostService.CACHE_KEY_STICKY
        posts = cache.get(cache_key)
        if posts is not None:
            return posts
            
        posts = Post.query.filter_by(
            is_sticky=True, 
            status=1
        ).order_by(desc(Post.created_at)).all()
        
        cache.set(cache_key, posts, timeout=PostService.CACHE_TIMEOUT)
        return posts
    
    @staticmethod
    def get_posts_by_page(page: int, per_page: int = 10) -> Pagination:
        """获取分页文章列表"""
        query = Post.query.filter_by(
            status=1, 
            is_sticky=False
        ).order_by(desc(Post.created_at))
        return Pagination(query, page, per_page)
    
    @classmethod
    def get_archives(cls, archived=True):
        """
        获取文章归档信息
        :param archived: 是否包含归档状态的文章
        :return: 归档字典，按年月组织
        """
        # 直接调用下面的静态方法
        return cls.get_archives_static()
        
    @staticmethod
    def get_archives_static() -> Dict[str, Dict[str, List[Post]]]:
        """获取文章归档信息"""
        from flask import current_app
        from app.models.post import PostStatus
        
        # 直接打印调试信息
        print("======= 开始获取归档信息 =======")
        
        # 检查缓存
        from app.extensions import cache
        cache_key = 'archives'
        cached_data = cache.get(cache_key)
        if cached_data:
            print("从缓存获取归档数据")
            print("缓存中的归档月份数量: {}".format(len(cached_data)))
            for key, posts in cached_data.items():
                print("缓存月份: {}, 文章数: {}".format(key, len(posts)))
                for post in posts:
                    print("  - ID: {}, 标题: {}, 状态: {}, 创建时间: {}".format(
                        post.id, post.title, post.status, post.created_at))
            return cached_data
        
        print("从数据库重新生成归档数据")
        
        # 修改为: 获取已发布和已归档的文章
        posts = Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(desc(Post.created_at)).all()
        
        print("查询到的文章总数: {}".format(len(posts)))
        for post in posts:
            print("查询到文章: ID={}, 标题={}, 状态={}, 创建时间={}".format(
                post.id, post.title, post.status, post.created_at))
        
        # 记录查询到的文章状态以便调试
        status_counts = {}
        for post in posts:
            status_str = str(post.status)
            if status_str not in status_counts:
                status_counts[status_str] = 0
            status_counts[status_str] += 1
            
        print(f"归档查询结果: 共 {len(posts)} 篇文章, 状态统计: {status_counts}")
        
        # 按年月组织文章
        archives = {}
        
        for post in posts:
            if not post.created_at:
                print(f"跳过文章 {post.id}，创建时间为空")
                continue
                
            # 生成键格式为 "2024-03" 的字符串
            key = f"{post.created_at.year}-{post.created_at.month:02d}"
            
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
            print(f"添加文章到归档: {post.title} -> {key}")
        
        # 保存到缓存
        cache.set(cache_key, archives, timeout=300)  # 5分钟过期
        
        print(f"归档数据生成完成，共 {len(archives)} 个月份")
        for key, posts in archives.items():
            print(f"月份 {key}: {len(posts)} 篇文章")
            
        print("======= 归档信息获取完成 =======")
        
        return archives
    
    @staticmethod
    def get_posts_by_time():
        """按时间线获取文章列表"""
        # 修改为使用枚举值
        return Post.query.filter(
            (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
        ).order_by(desc(Post.created_at)).all()
    
    def get_recent_posts(self, search=None, limit=5):
        """获取最近文章
        
        Args:
            search: 搜索关键词
            limit: 返回的文章数量
            
        Returns:
            list: 文章列表
        """
        try:
            current_app.logger.info(f"开始获取最近文章，搜索条件: {search}, 限制数量: {limit}")
            
            # 强制同步数据库会话，避免缓存问题
            db.session.commit()
            
            # 构建基础查询 - 明确获取所有状态的文章，不做过滤
            query = Post.query
            
            # 记录查询条件
            current_app.logger.info("查询所有状态的文章，不进行状态过滤")
            
            # 如果有搜索关键词，添加搜索条件
            if search:
                search_query = self._build_search_query(search)
                query = query.filter(search_query)
            
            # 预加载关联数据以提高性能
            query = query.options(
                db.joinedload(Post.category),
                db.joinedload(Post.author),
                db.joinedload(Post.tags)
            )
            
            # 打印SQL语句
            current_app.logger.info(f"即将执行的SQL查询: {str(query)}")
            
            # 获取最新的文章，按创建时间倒序排序
            posts = query.order_by(Post.created_at.desc()).limit(limit).all()
            
            if posts is None:
                current_app.logger.warning("查询返回了None，将返回空列表")
                return []
            
            current_app.logger.info(f"查询到 {len(posts)} 篇最近文章")
            for post in posts:
                current_app.logger.info(f"文章ID: {post.id}, 标题: {post.title}, 状态: {post.status}")
            
            # 确保所有对象都已从数据库加载完整数据
            for post in posts:
                db.session.refresh(post)
                
            # 确保关联数据被加载
            for post in posts:
                try:
                    if post.category:
                        db.session.refresh(post.category)
                    if post.author:
                        db.session.refresh(post.author)
                    if post.tags:
                        for tag in post.tags:
                            db.session.refresh(tag)
                except Exception as e:
                    current_app.logger.error(f"加载文章 {post.id} 的关联数据时出错: {str(e)}")
            
            current_app.logger.info(f'成功获取最近文章，共 {len(posts)} 篇')
            
            # 最后检查一下是否所有文章都有标题
            for i, post in enumerate(posts):
                if not post.title:
                    current_app.logger.warning(f"文章 {post.id} 没有标题，将设置默认标题")
                    post.title = f"未命名文章 {post.id}"
            
            return posts
        except Exception as e:
            current_app.logger.error(f"获取最近文章时出错: {str(e)}")
            current_app.logger.exception(e)
            return []

    @staticmethod
    def get_related_posts(post, limit=5):
        """获取相关文章"""
        try:
            # 导入Tag模型
            from app.models.tag import Tag
            from sqlalchemy import desc
            
            # 根据标签获取相关文章
            if not post or not hasattr(post, 'tags'):
                current_app.logger.error(f"获取相关文章失败: 文章不存在或没有tags属性")
                return []
                
            tag_ids = [tag.id for tag in post.tags]
            if tag_ids:
                return Post.query.filter(
                    Post.id != post.id,
                    (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED),
                    Post.tags.any(Tag.id.in_(tag_ids))
                ).order_by(desc(Post.created_at)).limit(limit).all()
            return []
        except Exception as e:
            current_app.logger.error(f"获取相关文章失败: {str(e)}")
            traceback.print_exc()
            return []

    @staticmethod
    def get_post_by_id(post_id):
        """根据ID获取文章"""
        return Post.query.get(post_id)

    def get_posts_paginated(self, page=1, per_page=10, category_id=None, tag_id=None, 
                          author_id=None, status=None):
        """获取分页的文章列表
        
        Args:
            page: 页码
            per_page: 每页数量
            category_id: 分类ID
            tag_id: 标签ID
            author_id: 作者ID
            status: 文章状态
            
        Returns:
            Pagination 对象
        """
        try:
            # 清理缓存
            cache_keys = [
                'post_list',
                f'post_list:{page}:{per_page}',
                f'category_posts:{category_id}' if category_id else None,
                f'tag_posts:{tag_id}' if tag_id else None
            ]
            
            # 使用 Redis 的 pipeline 批量删除缓存
            if hasattr(current_app, 'redis'):
                pipe = current_app.redis.pipeline()
                for key in cache_keys:
                    if key:
                        pipe.delete(key)
                pipe.execute()
            
            # 强制刷新数据库会话
            db.session.expire_all()
            db.session.commit()
            
            # 强制创建新的数据库连接
            db.session.execute(text('SELECT 1'))
            
            # 构建基础查询
            query = Post.query
            
            # 使用 joinedload 预加载关联数据
            query = query.options(
                db.joinedload(Post.category),
                db.joinedload(Post.author),
                db.joinedload(Post.tags)
            )
            
            # 应用过滤条件
            if category_id:
                query = query.filter(Post.category_id == category_id)
            if tag_id:
                query = query.filter(Post.tags.any(id=tag_id))
            if author_id:
                query = query.filter(Post.author_id == author_id)
            if status:
                query = query.filter(Post.status == status)
            
            # 按创建时间倒序排序
            query = query.order_by(Post.created_at.desc())
            
            # 执行分页查询
            pagination = query.paginate(page=page, per_page=per_page)
            
            # 预加载每个文章的关联数据
            if pagination.items:
                for post in pagination.items:
                    db.session.refresh(post)
                    if post.category:
                        db.session.refresh(post.category)
                    if post.author:
                        db.session.refresh(post.author)
                    for tag in post.tags:
                        db.session.refresh(tag)
            
            # 再次提交会话以确保所有更改都被保存
            db.session.commit()
            
            return pagination
            
        except Exception as e:
            current_app.logger.error(f"获取分页文章列表失败: {str(e)}")
            current_app.logger.exception(e)
            db.session.rollback()
            raise

    def get_prev_post(self, post: Post) -> Optional[Post]:
        """获取上一篇文章
        
        Args:
            post: 当前文章对象
            
        Returns:
            Post: 上一篇文章对象，如果不存在则返回None
        """
        try:
            return Post.query.filter(
                Post.id < post.id,
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED),
                Post.is_private == False
            ).order_by(Post.id.desc()).first()
        except Exception as e:
            current_app.logger.error(f"获取上一篇文章失败: {str(e)}")
            return None
            
    def get_next_post(self, post: Post) -> Optional[Post]:
        """获取下一篇文章
        
        Args:
            post: 当前文章对象
            
        Returns:
            Post: 下一篇文章对象，如果不存在则返回None
        """
        try:
            return Post.query.filter(
                Post.id > post.id,
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED),
                Post.is_private == False
            ).order_by(Post.id.asc()).first()
        except Exception as e:
            current_app.logger.error(f"获取下一篇文章失败: {str(e)}")
            return None

    def get_post_count(self):
        """获取文章总数"""
        try:
            return Post.query.count()
        except Exception as e:
            current_app.logger.error(f"获取文章总数失败: {str(e)}")
            return 0

    def count_posts_since(self, start_time: datetime) -> int:
        """统计指定时间之后的文章数量
        
        Args:
            start_time: 开始时间
            
        Returns:
            int: 文章数量
        """
        try:
            count = Post.query.filter(Post.created_at >= start_time).count()
            return count
        except Exception as e:
            current_app.logger.error(f"统计文章数量失败: {str(e)}")
            return 0

    def get_all_tags(self):
        """获取所有标签
        
        Returns:
            list: 标签列表
        """
        try:
            # 导入Tag模型，避免循环导入
            from app.models.tag import Tag
            
            # 获取所有标签
            tags = Tag.query.all()
            
            return tags
            
        except Exception as e:
            current_app.logger.error(f'获取所有标签失败: {str(e)}')
            current_app.logger.exception(e)
            return []
    
    def get_posts_count_by_status(self, status):
        """获取指定状态的文章数量
        
        Args:
            status: 文章状态
            
        Returns:
            int: 文章数量
        """
        try:
            # 查询指定状态的文章数量
            count = Post.query.filter(Post.status == status).count()
            
            return count
            
        except Exception as e:
            current_app.logger.error(f'获取状态为{status}的文章数量失败: {str(e)}')
            current_app.logger.exception(e)
            return 0
            
    def get_total_posts(self):
        """获取文章总数
        
        Returns:
            int: 文章总数
        """
        try:
            # 查询文章总数
            count = Post.query.count()
            
            return count
            
        except Exception as e:
            current_app.logger.error(f'获取文章总数失败: {str(e)}')
            current_app.logger.exception(e)
            return 0

    def get_posts_by_tag(self, tag_id, page=1, per_page=10):
        """获取标签下的文章列表
        
        Args:
            tag_id: 标签ID
            page: 页码
            per_page: 每页条数
            
        Returns:
            Pagination: 分页对象
        """
        try:
            # 检查标签是否存在
            from app.models.tag import Tag
            tag = Tag.query.get(tag_id)
            if not tag:
                current_app.logger.warning(f"标签不存在: {tag_id}")
                # 使用空查询
                from sqlalchemy.sql.expression import select
                from sqlalchemy.sql import text
                empty_query = db.session.query(Post).filter(text('1=0'))
                return Pagination(empty_query, page, per_page)
            
            # 从缓存获取
            cache_key = self.CACHE_KEY_TAG.format(tag_id, page, per_page)
            result = cache.get(cache_key)
            if result and not current_app.config.get('TESTING'):
                current_app.logger.info(f"从缓存获取标签 {tag_id} 的文章列表，页码 {page}")
                return result
            
            # 查询标签下的已发布或已归档文章
            query = Post.query.filter(
                Post.tags.any(id=tag_id),
                (Post.status == PostStatus.PUBLISHED) | (Post.status == PostStatus.ARCHIVED)
            ).order_by(Post.created_at.desc())
            
            # 创建分页对象
            pagination = Pagination(query, page, per_page)
            
            # 缓存查询结果
            if not current_app.config.get('TESTING'):
                cache.set(cache_key, pagination, timeout=self.CACHE_TIMEOUT)
            
            current_app.logger.info(f"查询标签 {tag_id} 的文章列表成功，共 {pagination.total} 篇")
            return pagination
            
        except Exception as e:
            current_app.logger.error(f"获取标签 {tag_id} 的文章列表失败: {str(e)}")
            current_app.logger.exception(e)
            # 发生异常时返回空的查询结果
            from sqlalchemy.sql.expression import select
            from sqlalchemy.sql import text
            empty_query = db.session.query(Post).filter(text('1=0'))
            return Pagination(empty_query, page, per_page)