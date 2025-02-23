"""
文件名：category.py
描述：分类服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.extensions import db
from app.models.category import Category
from app.services import SecurityService
from typing import List, Optional, Dict
from sqlalchemy import func

class CategoryService:
    """分类服务类"""
    
    def __init__(self):
        self.security = SecurityService()

    def create_category(self, name, slug=None, description=None):
        """创建分类
        
        Args:
            name: 分类名称
            slug: URL友好的名称（可选）
            description: 分类描述（可选）
            
        Returns:
            Category: 创建的分类对象
            
        Raises:
            ValueError: 如果分类名称已存在
        """
        if Category.query.filter_by(name=name).first():
            raise ValueError('分类名称已存在')
            
        category = Category(
            name=name,
            slug=slug,
            description=description
        )
        
        db.session.add(category)
        db.session.commit()
        
        return category

    def update_category(self, category_id: int, name: str = None, 
                       slug: str = None) -> Dict:
        """更新分类
        
        Args:
            category_id: 分类ID
            name: 新的分类名称
            slug: 新的分类别名
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            category = Category.query.get(category_id)
            if not category:
                return {'status': 'error', 'message': '分类不存在'}
                
            if name and name != category.name:
                # 检查新名称是否已存在
                if Category.query.filter_by(name=name).first():
                    return {'status': 'error', 'message': '分类名已存在'}
                category.name = name
                
            if slug and slug != category.slug:
                # 检查新别名是否已存在
                if Category.query.filter_by(slug=slug).first():
                    return {'status': 'error', 'message': '分类别名已存在'}
                category.slug = slug
                
            db.session.commit()
            return {'status': 'success', 'message': '分类更新成功', 'category': category}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'更新分类失败：{str(e)}'}
            
    def delete_category(self, category_id: int) -> Dict:
        """删除分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            category = Category.query.get(category_id)
            if not category:
                return {'status': 'error', 'message': '分类不存在'}
                
            # 检查是否有文章使用此分类
            if category.posts.count() > 0:
                return {'status': 'error', 'message': '该分类下还有文章，无法删除'}
                
            db.session.delete(category)
            db.session.commit()
            return {'status': 'success', 'message': '分类删除成功'}
            
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'删除分类失败：{str(e)}'}
            
    def get_all_categories(self) -> List[Category]:
        """获取所有分类
        
        Returns:
            list: 分类列表
        """
        return Category.query.all()
        
    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """根据ID获取分类
        
        Args:
            category_id: 分类ID
            
        Returns:
            Category: 分类对象
        """
        return Category.query.get(category_id)
        
    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """根据别名获取分类
        
        Args:
            slug: 分类别名
            
        Returns:
            Category: 分类对象
        """
        return Category.query.filter_by(slug=slug).first()
        
    def get_categories_with_post_count(self) -> List[Dict]:
        """获取分类及其文章数量
        
        Returns:
            list: 包含分类信息和文章数量的字典列表
        """
        from app.models import Post
        categories = Category.query.all()
        result = []
        
        for category in categories:
            post_count = Post.query.filter_by(
                category_id=category.id, 
                status=1
            ).count()
            result.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'post_count': post_count
            })
            
        return result

    def get_category_list(self, page=1, per_page=10):
        """获取分类列表（分页）
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 包含分页信息的字典
        """
        from app.models import Post
        
        pagination = Category.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        categories = []
        for category in pagination.items:
            post_count = Post.query.filter_by(
                category_id=category.id,
                status=1
            ).count()
            categories.append({
                'id': category.id,
                'name': category.name,
                'slug': category.slug,
                'post_count': post_count,
                'created_at': category.created_at
            })
            
        return {
            'items': categories,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }

    def search_categories(self, keyword, page=1, per_page=10):
        """搜索分类"""
        return Category.query.filter(
            Category.name.ilike(f'%{keyword}%')
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

    def get_category_stats(self):
        """获取分类统计信息"""
        total_categories = Category.query.count()
        categories_with_posts = Category.query.filter(
            Category.posts.any()
        ).count()
        
        # 获取每个分类的文章数量
        category_post_counts = []
        for category in Category.query.all():
            category_post_counts.append({
                'id': category.id,
                'name': category.name,
                'post_count': category.posts.count()
            })
        
        return {
            'total_categories': total_categories,
            'categories_with_posts': categories_with_posts,
            'category_post_counts': category_post_counts
        }

    @staticmethod
    def get_total_categories():
        """获取分类总数"""
        return Category.query.count()

    @staticmethod
    def get_posts_by_category(category_id, page=1, per_page=10):
        """获取分类下的文章列表（分页）"""
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            raise ValueError("分类不存在")
        
        return category.posts.order_by(
            db.desc('created_at')
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ) 