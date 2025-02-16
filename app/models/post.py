"""
文件名：post.py
描述：文章数据模型
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime
from app import db
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
    html_content = db.Column(db.Text)  # 存储转换后的HTML内容
    toc = db.Column(db.JSON)  # 存储文章目录结构
    summary = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0: 草稿, 1: 已发布
    is_sticky = db.Column(db.Boolean, default=False)  # 是否置顶
    view_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    category = db.relationship('Category', backref='posts')
    tags = db.relationship('Tag', secondary=post_tags, backref=db.backref('posts', lazy='dynamic'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """初始化时自动将Markdown内容转换为HTML"""
        if 'content' in kwargs:
            result = markdown_to_html(kwargs['content'])
            kwargs['html_content'] = result['html']
            kwargs['toc'] = result.get('toc', [])
        super(Post, self).__init__(**kwargs)
    
    def update_content(self, content):
        """更新文章内容时自动更新HTML内容"""
        self.content = content
        result = markdown_to_html(content)
        self.html_content = result['html']
        self.toc = result.get('toc', [])
    
    def __repr__(self):
        return f'<Post {self.title}>' 