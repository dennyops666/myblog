"""
文件名：tag.py
描述：标签模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC

# 文章-标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    extend_existing=True
)

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关系
    posts = db.relationship('Post', secondary=post_tags, back_populates='tags')
    
    def __init__(self, name, slug=None, description=None):
        self.name = name
        self.slug = slug or name.lower().replace(' ', '-')
        self.description = description
        
    def __repr__(self):
        return f'<Tag {self.name}>'