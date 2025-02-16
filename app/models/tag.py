"""
文件名：tag.py
描述：标签数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime
from app.extensions import db

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    posts = db.relationship('Post', secondary='post_tags', back_populates='tags', lazy='dynamic')
    
    def __repr__(self):
        return f'<Tag {self.name}>' 