"""
文件名：category_service.py
描述：分类服务类
作者：denny
创建日期：2025-02-16
"""

from sqlalchemy import desc
from app.models import Category, db

class CategoryService:
    @staticmethod
    def create_category(name, description=None):
        """创建新分类"""
        if not name:
            raise ValueError("分类名称不能为空")
        if len(name) > 50:
            raise ValueError("分类名称不能超过50个字符")
        
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def get_category_by_id(category_id):
        """根据ID获取分类"""
        return db.session.get(Category, category_id)
    
    @staticmethod
    def get_all_categories():
        """获取所有分类"""
        return Category.query.order_by(Category.name).all()
    
    @staticmethod
    def get_total_categories():
        """获取分类总数"""
        return Category.query.count()
    
    @staticmethod
    def update_category(category, **kwargs):
        """更新分类"""
        for key, value in kwargs.items():
            if hasattr(category, key):
                setattr(category, key, value)
        db.session.commit()
        return category
    
    @staticmethod
    def delete_category(category):
        """删除分类"""
        if category.posts.count() > 0:
            raise Exception("该分类下还有文章，无法删除")
        db.session.delete(category)
        db.session.commit()
    
    @staticmethod
    def get_posts_by_category(category_id, page=1, per_page=10):
        """获取分类下的文章列表（分页）"""
        category = CategoryService.get_category_by_id(category_id)
        if not category:
            raise ValueError("分类不存在")
        
        return category.posts.order_by(
            desc('created_at')
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ) 