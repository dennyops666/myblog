"""
文件名：post.py
描述：文章服务类
作者：denny
创建日期：2025-02-16
"""

import os
from datetime import datetime
from werkzeug.utils import secure_filename
from sqlalchemy import desc, extract
from app.models import Post, db
from app.utils.pagination import Pagination
from app.config import Config

class PostService:
    @staticmethod
    def get_sticky_posts():
        """获取置顶文章列表"""
        return Post.query.filter_by(is_sticky=True, status=1).order_by(desc(Post.created_at)).all()
    
    @staticmethod
    def get_posts_by_page(page, per_page=10):
        """获取分页文章列表"""
        query = Post.query.filter_by(status=1, is_sticky=False).order_by(desc(Post.created_at))
        return Pagination(query, page, per_page)
    
    @staticmethod
    def get_archives():
        """获取文章归档信息"""
        posts = Post.query.filter_by(status=1).order_by(desc(Post.created_at)).all()
        archives = {}
        
        for post in posts:
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
    def get_post_by_id(post_id):
        """根据ID获取文章"""
        return Post.query.get(post_id)
    
    @staticmethod
    def get_related_posts(post, limit=5):
        """获取相关文章"""
        # 根据标签获取相关文章
        tag_ids = [tag.id for tag in post.tags]
        related_posts = Post.query.filter(
            Post.id != post.id,
            Post.status == 1,
            Post.tags.any(id=tag_ids)
        ).order_by(desc(Post.created_at)).limit(limit).all()
        
        return related_posts
    
    @staticmethod
    def get_prev_next_post(post):
        """获取上一篇和下一篇文章"""
        prev_post = Post.query.filter(
            Post.id < post.id,
            Post.status == 1
        ).order_by(desc(Post.id)).first()
        
        next_post = Post.query.filter(
            Post.id > post.id,
            Post.status == 1
        ).order_by(Post.id).first()
        
        return prev_post, next_post
    
    @staticmethod
    def upload_image(file, post_id=None):
        """上传图片
        
        Args:
            file: FileStorage对象
            post_id: 关联的文章ID（可选）
            
        Returns:
            str: 图片URL
        """
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
        unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file_path = os.path.join(save_dir, unique_filename)
        
        # 保存文件
        file.save(file_path)
        
        # 返回可访问的URL
        return f'/uploads/images/{unique_filename}'
    
    @staticmethod
    def _allowed_file(filename):
        """检查文件类型是否允许"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_post_images(post_id):
        """获取文章关联的图片列表"""
        post = Post.query.get(post_id)
        if not post:
            return []
            
        # TODO: 实现图片关联关系
        return []
    
    @staticmethod
    def delete_image(image_path):
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
    def get_posts_by_category(category_id, page=1, per_page=10):
        """获取分类下的文章列表
        
        Args:
            category_id: 分类ID
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        query = Post.query.filter_by(
            category_id=category_id,
            status=1
        ).order_by(desc(Post.created_at))
        return Pagination(query, page, per_page)
    
    @staticmethod
    def get_posts_by_tag(tag_id, page=1, per_page=10):
        """获取标签下的文章列表
        
        Args:
            tag_id: 标签ID
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        query = Post.query.filter(
            Post.status == 1,
            Post.tags.any(id=tag_id)
        ).order_by(desc(Post.created_at))
        return Pagination(query, page, per_page)
    
    @staticmethod
    def get_posts_by_time(year=None, month=None, page=1, per_page=10):
        """按时间线获取文章列表
        
        Args:
            year: 年份
            month: 月份
            page: 页码
            per_page: 每页数量
            
        Returns:
            Pagination: 分页对象
        """
        query = Post.query.filter_by(status=1)
        
        if year:
            query = query.filter(extract('year', Post.created_at) == year)
        if month:
            query = query.filter(extract('month', Post.created_at) == month)
            
        query = query.order_by(desc(Post.created_at))
        return Pagination(query, page, per_page) 