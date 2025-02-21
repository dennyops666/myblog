"""
文件名：post.py
描述：文章服务
作者：denny
创建日期：2024-03-21
"""

import os
from datetime import datetime, UTC
from werkzeug.utils import secure_filename
from sqlalchemy import desc, extract, or_, and_, func, text
from app.models import Post, db, Category, Tag
from app.models.post import PostStatus
from app.utils.pagination import Pagination
from app.config import Config
from app.utils.markdown import markdown_to_html
from app.extensions import cache
from typing import List, Dict, Any, Optional, Tuple
import re
from flask import current_app
from app.services.security import SecurityService
from PIL import Image
import uuid
import secrets
from flask import url_for
import json

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

    def get_post_images(self, post_content):
        """获取文章中的图片URL列表
        
        Args:
            post_content: 文章内容
            
        Returns:
            list: 图片URL列表
        """
        if not post_content:
            return []
        
        # 匹配Markdown图片语法
        pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(pattern, post_content)
        return matches

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

    @staticmethod
    def _clear_post_cache(post_id: int) -> None:
        """清理文章相关的所有缓存"""
        # 清理单篇文章缓存
        cache.delete(PostService.CACHE_KEY_POST.format(post_id))
        
        # 清理置顶文章缓存
        cache.delete(PostService.CACHE_KEY_STICKY)
        
        # 清理分类文章缓存
        post = PostService.get_post(post_id)
        if post and post.category_id:
            # 清理该分类下所有页的缓存
            for page in range(1, PostService.MAX_CACHE_PAGES + 1):
                cache.delete(PostService.CACHE_KEY_CATEGORY.format(
                    post.category_id, page, 10
                ))
        
        # 清理标签文章缓存
        if post and post.tags:
            for tag in post.tags:
                for page in range(1, PostService.MAX_CACHE_PAGES + 1):
                    cache.delete(PostService.CACHE_KEY_TAG.format(
                        tag.id, page, 10
                    ))
        
        # 清理时间归档缓存
        if post and post.created_at:
            year = post.created_at.year
            month = post.created_at.month
            for page in range(1, PostService.MAX_CACHE_PAGES + 1):
                cache.delete(PostService.CACHE_KEY_TIME.format(
                    year, month, page, 10
                ))
        
        # 清理相关文章缓存
        cache.delete(PostService.CACHE_KEY_RELATED.format(post_id, 5))
    
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
    
    def create_post(self, title, content, author=None, author_id=None, category_id=None, tags=None, status=PostStatus.DRAFT):
        """创建文章
        
        Args:
            title: 文章标题
            content: 文章内容
            author: 作者对象（可选）
            author_id: 作者ID（可选）
            category_id: 分类ID（可选）
            tags: 标签列表（可选）
            status: 文章状态（可选，默认为草稿）
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            from app.utils.markdown import MarkdownService
            
            # 清理输入
            title = self.security_service.sanitize_input(title)
            content = self.security_service.sanitize_markdown(content) if content else ''
            
            # 生成HTML内容和摘要
            markdown_service = MarkdownService()
            result = markdown_service.convert(content)
            
            # 生成摘要（取前200个字符）
            text_content = ''.join(content.split('\n')[:3])  # 取前三行
            summary = text_content[:200] + '...' if len(text_content) > 200 else text_content
            
            # 创建文章
            post = Post(
                title=title,
                content=content,
                html_content=result['html'],
                _toc=json.dumps(result['toc']),
                summary=summary,
                status=status,
                is_private=False
            )
            
            # 设置作者
            if author:
                post.author = author
            elif author_id:
                from app.models import User
                author = User.query.get(author_id)
                if author:
                    post.author = author
                else:
                    return {'status': 'error', 'message': '作者不存在'}
            
            # 设置分类
            if category_id:
                from app.models import Category
                category = Category.query.get(category_id)
                if category:
                    post.category = category
                    
            # 设置标签
            if tags:
                from app.models import Tag
                for tag_name in tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
                    
            db.session.add(post)
            db.session.commit()
            
            return {'status': 'success', 'message': '文章创建成功', 'post': post}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建文章失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
            
    def update_post(self, post_id, title=None, content=None, category_id=None, tags=None, status=None):
        """更新文章
        
        Args:
            post_id: 文章ID
            title: 新标题
            content: 新内容
            category_id: 新分类ID
            tags: 新标签列表
            status: 新状态
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return {'status': 'error', 'message': '文章不存在'}
                
            # 更新标题
            if title:
                post.title = self.security_service.sanitize_input(title)
                
            # 更新内容
            if content:
                post.content = self.security_service.sanitize_markdown(content)
                
            # 更新分类
            if category_id:
                category = Category.query.get(category_id)
                if category:
                    post.category = category
                    
            # 更新状态
            if status is not None:
                post.status = PostStatus.PUBLISHED if status == 1 else PostStatus.DRAFT
                
            # 更新标签
            if tags:
                post.tags.clear()
                for tag_name in tags:
                    tag = Tag.query.filter_by(name=tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        db.session.add(tag)
                    post.tags.append(tag)
                    
            post.updated_at = datetime.now(UTC)
            db.session.commit()
            
            return {'status': 'success', 'message': '文章更新成功', 'post': post}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新文章失败: {str(e)}")
            return {'status': 'error', 'message': '更新文章失败，请稍后重试'}
            
    def delete_post(self, post_id):
        """删除文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return {'status': 'error', 'message': '文章不存在'}
                
            db.session.delete(post)
            db.session.commit()
            
            return {'status': 'success', 'message': '文章删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除文章失败: {str(e)}")
            return {'status': 'error', 'message': '删除文章失败，请稍后重试'}
            
    def get_post(self, post_id):
        """获取文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return {'status': 'error', 'message': '文章不存在'}
                
            return {'status': 'success', 'post': post}
            
        except Exception as e:
            current_app.logger.error(f"获取文章失败: {str(e)}")
            return {'status': 'error', 'message': '获取文章失败，请稍后重试'}
            
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

    def get_post_list(self, page=1, per_page=10, category=None, tag=None, author=None, 
                     include_private=False):
        """获取文章列表
        
        Args:
            page: 页码
            per_page: 每页数量
            category: 分类ID
            tag: 标签名
            author: 作者ID
            include_private: 是否包含私密文章
            
        Returns:
            dict: 包含分页信息的字典
        """
        query = Post.query
        
        if not include_private:
            query = query.filter_by(is_private=False)
        
        if category:
            query = query.filter_by(category_id=category)
        
        if tag:
            query = query.filter(Post.tags.any(name=tag))
        
        if author:
            query = query.filter_by(author_id=author)
        
        pagination = query.order_by(Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }

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
            post = self.get_post_by_id(post_id)
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
    def get_post(post_id: int) -> Optional[Post]:
        """获取文章"""
        cache_key = PostService.CACHE_KEY_POST.format(post_id)
        post = cache.get(cache_key)
        if post is not None:
            return post
        
        post = db.session.get(Post, post_id)
        if post:
            cache.set(cache_key, post, timeout=PostService.CACHE_TIMEOUT)
        return post
    
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
        """获取上一篇和下一篇文章"""
        prev_post = Post.query.filter(
            Post.created_at < post.created_at,
            Post.status == 1
        ).order_by(desc(Post.created_at)).first()
        
        next_post = Post.query.filter(
            Post.created_at > post.created_at,
            Post.status == 1
        ).order_by(Post.created_at).first()
        
        return prev_post, next_post
    
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
    def get_prev_next_post(post):
        """获取上一篇和下一篇文章"""
        prev_post = Post.query.filter(
            Post.status == 1,
            Post.created_at < post.created_at
        ).order_by(Post.created_at.desc()).first()
        
        next_post = Post.query.filter(
            Post.status == 1,
            Post.created_at > post.created_at
        ).order_by(Post.created_at.asc()).first()
        
        return {
            'prev': prev_post,
            'next': next_post
        }

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

    def get_post_by_id(self, post_id):
        """根据ID获取文章
        
        Args:
            post_id: 文章ID
            
        Returns:
            Post: 文章对象
        """
        return Post.query.get(post_id)