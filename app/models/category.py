"""
文件名：category.py
描述：分类模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC

class Category(db.Model):
    """分类模型"""
    __tablename__ = 'categories'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关系
    posts = db.relationship('Post', back_populates='category', lazy='dynamic')
    
    def __init__(self, name, slug=None, description=None):
        self.name = name
        self.slug = slug or name.lower().replace(' ', '-')
        self.description = description
        
    def __repr__(self):
        return f'<Category {self.name}>' 