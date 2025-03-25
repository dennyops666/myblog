"""
文件名：tag.py
描述：标签模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC
from flask import current_app
from app.models.associations import post_tags
import re

class Tag(db.Model):
    """标签模型"""
    __tablename__ = 'tags'
    __table_args__ = (
        db.Index('idx_tag_name', 'name'),
        db.Index('idx_tag_slug', 'slug'),
        db.CheckConstraint("name != '' AND slug != ''", name='chk_tag_not_empty'),
        {'extend_existing': True}
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    slug = db.Column(db.String(64), unique=True, nullable=True)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    
    # 关系
    posts = db.relationship(
        'Post',
        secondary=post_tags,
        back_populates='tags',
        lazy='select',  # 使用 select 加载策略
        cascade='all, delete',
        passive_deletes=True
    )
    
    _post_count = None
    
    def __init__(self, name, slug=None, description=None):
        self.name = name.strip()
        if slug:
            self.slug = slug.strip()
        else:
            # 生成slug：转换为小写，替换空格为连字符，移除特殊字符
            self.slug = re.sub(r'[^\w\-]', '', name.lower().replace(' ', '-'))
        self.description = description.strip() if description else None
    
    @property
    def post_count(self):
        """获取标签下的文章数量"""
        if self._post_count is None:
            from app.models.post import Post, PostStatus
            
            current_app.logger.info(f"计算标签 '{self.name}' 的文章数量...")
            self._post_count = Post.query.join(Post.tags).filter(
                Post.status == PostStatus.PUBLISHED,
                Tag.id == self.id
            ).count()
            current_app.logger.info(f"标签 '{self.name}' 的文章数量: {self._post_count}")
            
        return self._post_count
    
    @post_count.setter
    def post_count(self, value):
        """设置标签下的文章数量"""
        self._post_count = value
    
    def __repr__(self):
        return f'<Tag {self.name}>'