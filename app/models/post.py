"""
文件名：post.py
描述：文章数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
from app.utils.markdown import markdown_to_html

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
    html_content = db.Column(db.Text)  # 存储解析后的HTML内容
    toc = db.Column(db.JSON)  # 存储目录结构
    summary = db.Column(db.Text)  # 文章摘要
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0: 草稿, 1: 已发布
    is_sticky = db.Column(db.Boolean, default=False)  # 是否置顶
    view_count = db.Column(db.Integer, default=0)  # 浏览次数
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关联关系
    category = db.relationship('Category', back_populates='posts')
    author = db.relationship('User', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic')
    tags = db.relationship('Tag', secondary=post_tags, back_populates='posts')
    
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
    
    def __repr__(self):
        return f'<Post {self.title}>' 