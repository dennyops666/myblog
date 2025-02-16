"""
文件名：category_service.py
描述：分类服务类
作者：denny
创建日期：2025-02-16
"""

from app.models import Category, db

class CategoryService:
    @staticmethod
    def create_category(name, description=None):
        """创建新分类"""
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        return category
    
    @staticmethod
    def get_category_by_id(category_id):
        """根据ID获取分类"""
        return Category.query.get(category_id)
    
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
        db.session.delete(category)
        db.session.commit() 