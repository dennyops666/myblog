"""
文件名：category.py
描述：分类数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime
from app.extensions import db

class Category(db.Model):
    """分类模型"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    posts = db.relationship('Post', back_populates='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<Category {self.name}>' 