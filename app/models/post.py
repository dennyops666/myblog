"""
文件名：post.py
描述：文章数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
from app.utils.markdown import markdown_to_html
import json

# 文章标签关联表
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)

class Post(db.Model):
    """文章模型"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    _toc = db.Column('toc', db.Text, nullable=False, default='[]')
    summary = db.Column(db.String(500), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)  # 允许为空
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)  # 0: 草稿, 1: 已发布
    is_sticky = db.Column(db.Boolean, nullable=False, default=False)
    view_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关联关系
    category = db.relationship('Category', back_populates='posts')
    author = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic', cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='post_tags', back_populates='posts')
    
    @property
    def comment_count(self):
        """获取文章的评论数量"""
        from app.models import Comment
        return Comment.query.filter_by(
            post_id=self.id,
            status=0  # 包含待审核的评论
        ).count()
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        self.update_html_content()
    
    def update_html_content(self):
        """更新HTML内容和目录"""
        if self.content:
            result = markdown_to_html(self.content)
            self.html_content = result['html']
            self.toc = result['toc']
            # 生成摘要（取前200个字符）
            text_content = ''.join(self.content.split('\n')[:3])  # 取前三行
            self.summary = text_content[:200] + '...' if len(text_content) > 200 else text_content
    
    @property
    def toc(self):
        """获取目录结构"""
        return json.loads(self._toc)
        
    @toc.setter
    def toc(self, value):
        """设置目录结构"""
        self._toc = json.dumps(value)
    
    def get_toc(self):
        """获取目录结构（兼容方法）"""
        return self.toc
    
    def __repr__(self):
        return f'<Post {self.title}>' 