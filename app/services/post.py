"""
文件名：post.py
描述：文章服务类
作者：denny
创建日期：2025-02-16
"""

import os
from datetime import datetime, UTC
from werkzeug.utils import secure_filename
from sqlalchemy import desc, extract, or_, and_, func, text
from app.models import Post, db, Category, Tag
from app.utils.pagination import Pagination
from app.config import Config
from app.utils.markdown import markdown_to_html
from app.extensions import cache
from typing import List, Dict, Any, Optional, Tuple
import re

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
    
    @staticmethod
    def create_post(title: str, content: str, category_id: int, 
                   author_id: int, status: int = 1, 
                   is_sticky: bool = False) -> Post:
        """创建新文章"""
        try:
            if not title or not content:
                raise ValueError("标题和内容不能为空")
            
            # 验证分类ID
            category = db.session.get(Category, category_id)
            if not category:
                raise ValueError("无效的分类ID")
            
            # 解析Markdown内容
            parsed = markdown_to_html(content)
            
            post = Post(
                title=title,
                content=content,
                html_content=parsed['html'],
                toc=parsed['toc'],
                category_id=category_id,
                author_id=author_id,
                status=status,
                is_sticky=is_sticky,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            db.session.add(post)
            db.session.commit()
            return post
            
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"文章创建失败：{str(e)}")
    
    @staticmethod
    def update_post(post_id: int, **kwargs: Any) -> Post:
        """更新文章"""
        try:
            post = db.session.get(Post, post_id)
            if not post:
                raise ValueError("文章不存在")
            
            # 更新字段
            for key, value in kwargs.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            
            # 如果更新了内容，重新生成HTML
            if 'content' in kwargs:
                post.update_html_content()
            
            # 更新时间戳
            post.updated_at = datetime.now(UTC)
            
            db.session.commit()
            
            # 清理相关缓存
            PostService._clear_post_cache(post_id)
            
            return post
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"更新文章失败：{str(e)}")
    
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
    def upload_image(file: Any, post_id: Optional[int] = None) -> str:
        """上传图片"""
        if not file:
            raise ValueError('没有文件上传')
            
        # 验证文件类型
        filename = secure_filename(file.filename)
        if not PostService._allowed_file(filename):
            raise ValueError('不支持的文件类型')
            
        # 生成文件保存路径
        save_dir = os.path.join(Config.UPLOAD_FOLDER, 'images')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 生成唯一文件名
        unique_filename = f"{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(save_dir, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 返回可访问的URL
        return f'/uploads/images/{unique_filename}'
    
    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """检查文件类型是否允许"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_post_images(post_id: int) -> List[str]:
        """获取文章关联的图片列表"""
        post = Post.query.get(post_id)
        if not post:
            return []
            
        # TODO: 实现图片关联关系
        return []
    
    @staticmethod
    def delete_image(image_path: str) -> bool:
        """删除图片"""
        try:
            full_path = os.path.join(Config.UPLOAD_FOLDER, image_path.lstrip('/uploads/'))
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            return False
        return False
    
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