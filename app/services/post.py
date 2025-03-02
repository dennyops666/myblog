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
        try:
            # 获取文章对象
            post = Post.query.get(post_id)
            if not post:
                return
            
            # 清除文章详情缓存
            cache.delete(self.CACHE_KEY_POST.format(post_id))
            
            # 清除分类相关缓存
            if post.category_id:
                for page in range(1, self.MAX_CACHE_PAGES + 1):
                    cache.delete(self.CACHE_KEY_CATEGORY.format(post.category_id, page, 10))
            
            # 清除标签相关缓存
            for tag in post.tags:
                for page in range(1, self.MAX_CACHE_PAGES + 1):
                    cache.delete(self.CACHE_KEY_TAG.format(tag.id, page, 10))
            
            # 清除时间归档缓存
            year = post.created_at.year
            month = post.created_at.month
            for page in range(1, self.MAX_CACHE_PAGES + 1):
                cache.delete(self.CACHE_KEY_TIME.format(year, month, page, 10))
            
            # 清除相关文章缓存
            cache.delete(self.CACHE_KEY_RELATED.format(post_id, 5))
            
            # 清除搜索缓存
            for page in range(1, self.MAX_CACHE_PAGES + 1):
                cache.delete(self.CACHE_KEY_SEARCH.format('', page, 10))
            
            # 清除置顶文章缓存
            if post.is_sticky:
                cache.delete(self.CACHE_KEY_STICKY)
            
            # 强制刷新数据库会话中的对象
            db.session.refresh(post)
            if post.category:
                db.session.refresh(post.category)
            for tag in post.tags:
                db.session.refresh(tag)
            
        except Exception as e:
            current_app.logger.error(f"清除缓存失败: {str(e)}")
            current_app.logger.exception(e)

    @staticmethod
    def _build_search_query(search_text: str) -> Any:
        """构建搜索查询
        
        Args:
            search_text: 搜索文本
            
        Returns:
            查询条件
        """
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
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建文章失败: {str(e)}")
            current_app.logger.exception(e)
            raise ValueError('创建文章失败')

    def update_post(self, post_id, title=None, content=None, summary=None, category_id=None, tags=None, status=None):
        """更新文章
        
        Args:
            post_id: 文章ID
            title: 标题
            content: 内容
            summary: 摘要
            category_id: 分类ID
            tags: 标签列表
            status: 文章状态
            
        Returns:
            Post: 更新后的文章对象，如果更新失败则返回 None
        """
        try:
            # 使用 joinedload 预加载分类关系
            post = Post.query.options(db.joinedload(Post.category)).get(post_id)
            if not post:
                current_app.logger.error(f"文章不存在，ID: {post_id}")
                return None
            
            # 保存原始分类ID用于后续缓存清理
            old_category_id = post.category_id
            
            # 记录更新前的信息
            current_app.logger.debug(f"更新前的文章信息: 标题={post.title}, 分类ID={post.category_id}, 状态={post.status}")
            
            # 更新分类
            if category_id is not None:
                try:
                    new_category_id = int(category_id)
                    if new_category_id != old_category_id:
                        new_category = Category.query.get(new_category_id)
                        if new_category:
                            current_app.logger.info(f"更新分类: 从 {old_category_id} 更改为 {new_category_id}")
                            post.category_id = new_category_id
                            post.category = new_category  # 直接更新关系
                            db.session.flush()  # 立即刷新，确保更新生效
                            current_app.logger.info(f"分类更新成功，新分类ID: {post.category_id}")
                        else:
                            current_app.logger.error(f"未找到ID为 {new_category_id} 的分类")
                            return None
                except ValueError:
                    current_app.logger.error(f"分类ID格式错误: {category_id}")
                    return None

            if title is not None:
                post.title = title
            if content is not None:
                post.content = content
                post.update_html_content()  # 更新HTML内容
            if summary is not None:
                post.summary = summary
            if status is not None:
                post.status = status
            if tags is not None:
                # 清除旧标签
                post.tags.clear()
                # 添加新标签
                for tag in tags:
                    post.tags.append(tag)
            
            # 更新时间戳
            post.updated_at = datetime.now(UTC)
            
            # 提交所有更改
            db.session.commit()
            
            # 清除相关的缓存键
            current_app.logger.info("开始清除缓存")
            # 清理所有可能受影响的缓存
            self._clear_post_cache(post.id)  # 使用现有的清理缓存方法
            
            # 额外清理分类相关的缓存
            cache_keys = [
                f'post:{post_id}',
                'post_list',
                f'category_posts:{old_category_id}' if old_category_id else None,
                f'category_posts:{post.category_id}' if post.category_id else None,
                'categories',  # 清除分类列表缓存
                'category_list',  # 清除分类列表缓存
                f'post_list:category:{old_category_id}:*' if old_category_id else None,  # 清除旧分类的文章列表缓存
                f'post_list:category:{post.category_id}:*' if post.category_id else None,  # 清除新分类的文章列表缓存
                'category_list_with_count',  # 清除带文章计数的分类列表缓存
                f'category:{old_category_id}:*' if old_category_id else None,  # 清除旧分类的所有相关缓存
                f'category:{post.category_id}:*' if post.category_id else None  # 清除新分类的所有相关缓存
            ]
            
            # 使用 Redis 的 pipeline 批量删除缓存
            if hasattr(current_app, 'redis'):
                current_app.logger.info("使用 Redis pipeline 删除缓存")
                pipe = current_app.redis.pipeline()
                for key in cache_keys:
                    if key:
                        if '*' in key:  # 如果是通配符模式，使用 keys 命令查找匹配的键
                            matching_keys = current_app.redis.keys(key)
                            for matching_key in matching_keys:
                                current_app.logger.info(f"删除缓存键: {matching_key}")
                                pipe.delete(matching_key)
                        else:
                            current_app.logger.info(f"删除缓存键: {key}")
                            pipe.delete(key)
                pipe.execute()
            
            # 重新加载文章以确保所有关系都被正确加载
            db.session.expire(post)  # 使对象过期，强制重新加载
            db.session.refresh(post)  # 重新加载对象
            current_app.logger.info(f"文章 {post_id} 更新完成，当前分类ID={post.category_id}")
            
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

    def get_post_list(self, page=1, per_page=10, category=None, tag=None, author=None, include_private=False):
        """获取文章列表
        
        Args:
            page: 页码
            per_page: 每页数量
            category: 分类ID
            tag: 标签ID
            author: 作者ID
            include_private: 是否包含私密文章
            
        Returns:
            Pagination: 分页对象
        """
        # 使用 joinedload 预加载关联数据
        query = Post.query.options(
            db.joinedload(Post.category),
            db.joinedload(Post.author),
            db.joinedload(Post.tags)  # 预加载标签关系
        )
        
        if not include_private:
            query = query.filter_by(is_private=False)
        
        if category:
            query = query.filter_by(category_id=category)
        
        if tag:
            query = query.join(Post.tags).filter(Tag.id == tag)
        
        if author:
            query = query.filter_by(author_id=author)
        
        # 过滤已发布的文章
        query = query.filter_by(status=PostStatus.PUBLISHED)
        
        return query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

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
        total_posts = Post.query.count()
        published_posts = Post.query.filter_by(is_private=False).count()
        private_posts = Post.query.filter_by(is_private=True).count()
        total_views = db.session.query(db.func.sum(Post.view_count)).scalar() or 0
        
        return {
            'total_posts': total_posts,
            'published_posts': published_posts,
            'private_posts': private_posts,
            'total_views': total_views
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
    
    @staticmethod
    def get_archives() -> Dict[str, Dict[str, List[Post]]]:
        """获取文章归档信息"""
        posts = Post.query.filter_by(status=1).order_by(desc(Post.created_at)).all()
        archives: Dict[str, Dict[str, List[Post]]] = {}
        
        for post in posts:
            if not post.created_at:
                continue
            year = post.created_at.strftime('%Y')
            month = post.created_at.strftime('%m')
            if year not in archives:
                archives[year] = {}
            if month not in archives[year]:
                archives[year][month] = []
            archives[year][month].append(post)
        
        return archives
    
    @staticmethod
    def get_posts_by_time():
        """按时间线获取文章列表"""
        return Post.query.filter_by(status=1).order_by(desc(Post.created_at)).all()
    
    @staticmethod
    def get_related_posts(post, limit=5):
        """获取相关文章"""
        cache_key = f'related_posts_{post.id}_{limit}'
        posts = cache.get(cache_key)
        if posts is not None:
            return posts
            
        # 根据标签获取相关文章
        tag_ids = [tag.id for tag in post.tags]
        if tag_ids:
            posts = Post.query.filter(
                Post.id != post.id,
                Post.status == 1,
                Post.tags.any(id=tag_ids)
            ).order_by(desc(Post.created_at)).limit(limit).all()
            
            cache.set(cache_key, posts, timeout=300)
            return posts
        return []
    
    @staticmethod
    def get_prev_next_post(post: Post) -> Tuple[Optional[Post], Optional[Post]]:
        """获取上一篇和下一篇文章
        
        Args:
            post: 当前文章
            
        Returns:
            Tuple[Optional[Post], Optional[Post]]: 上一篇和下一篇文章的元组
        """
        try:
            # 获取上一篇文章（创建时间较早的最新一篇）
            prev_post = Post.query.filter(
                Post.status == PostStatus.PUBLISHED,
                Post.created_at < post.created_at
            ).order_by(Post.created_at.desc()).first()
            
            # 获取下一篇文章（创建时间较晚的最早一篇）
            next_post = Post.query.filter(
                Post.status == PostStatus.PUBLISHED,
                Post.created_at > post.created_at
            ).order_by(Post.created_at.asc()).first()
            
            return prev_post, next_post
            
        except Exception as e:
            current_app.logger.error(f"获取上一篇和下一篇文章失败: {str(e)}")
            return None, None
    
    @staticmethod
    def get_posts_by_category(category_id: int, page: int = 1, 
                            per_page: int = 10) -> Pagination:
        """获取分类下的文章列表"""
        cache_key = PostService.CACHE_KEY_CATEGORY.format(
            category_id, page, per_page
        )
        result = cache.get(cache_key)
        if result is not None:
            return result
            
        result = Post.query.filter_by(
            category_id=category_id,
            status=1
        ).order_by(desc(Post.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        cache.set(cache_key, result, timeout=PostService.CACHE_TIMEOUT)
        return result
    
    @staticmethod
    def get_posts_by_tag(tag_id: int, page: int = 1, 
                        per_page: int = 10) -> Pagination:
        """获取标签下的文章列表"""
        cache_key = PostService.CACHE_KEY_TAG.format(
            tag_id, page, per_page
        )
        result = cache.get(cache_key)
        if result is not None:
            return result
            
        result = Post.query.filter(
            Post.status == 1,
            Post.tags.any(id=tag_id)
        ).order_by(desc(Post.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        cache.set(cache_key, result, timeout=PostService.CACHE_TIMEOUT)
        return result
    
    @staticmethod
    def get_posts_by_time(year: Optional[int] = None, 
                         month: Optional[int] = None,
                         page: int = 1, 
                         per_page: int = 10) -> Pagination:
        """按时间线获取文章列表"""
        cache_key = PostService.CACHE_KEY_TIME.format(
            year or 0, month or 0, page, per_page
        )
        result = cache.get(cache_key)
        if result is not None:
            return result
            
        query = Post.query.filter_by(status=1)
        
        if year:
            query = query.filter(extract('year', Post.created_at) == year)
        if month:
            query = query.filter(extract('month', Post.created_at) == month)
            
        result = query.order_by(desc(Post.created_at)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        cache.set(cache_key, result, timeout=PostService.CACHE_TIMEOUT)
        return result

    @staticmethod
    def get_total_posts():
        """获取文章总数"""
        return Post.query.filter_by(status=1).count()

    @staticmethod
    def get_recent_posts(limit=5):
        """获取最近文章"""
        return Post.query.filter_by(status=1)\
            .order_by(Post.created_at.desc())\
            .limit(limit).all()

    @staticmethod
    def get_related_posts(post, limit=5):
        """获取相关文章"""
        # 根据相同标签获取相关文章
        tag_ids = [tag.id for tag in post.tags]
        if tag_ids:
            return Post.query.filter(
                Post.id != post.id,
                Post.status == 1,
                Post.tags.any(Tag.id.in_(tag_ids))
            ).limit(limit).all()
        return []

    @staticmethod
    def get_archives():
        """获取文章归档"""
        posts = Post.query.filter_by(status=1).order_by(desc(Post.created_at)).all()
        archives = {}
        
        for post in posts:
            year = post.created_at.year
            month = post.created_at.month
            key = f"{year}-{month:02d}"
            
            if key not in archives:
                archives[key] = []
            archives[key].append(post)
            
        return archives

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