"""
文件名：comment.py
描述：评论数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
from app.utils.markdown import MarkdownService

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text)  # 存储解析后的HTML内容
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 允许为空以支持匿名评论
    nickname = db.Column(db.String(50))  # 匿名评论者的昵称
    email = db.Column(db.String(120))  # 匿名评论者的邮箱
    status = db.Column(db.Integer, default=0)  # 0: 待审核, 1: 已通过
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # 关联关系
    post = db.relationship('Post', back_populates='comments')
    author = db.relationship('User', foreign_keys=[author_id], back_populates='comments')
    
    # 自引用关系
    replies = db.relationship('Comment',
                            back_populates='parent',
                            cascade='all',
                            remote_side=[id])
    parent = db.relationship('Comment',
                           back_populates='replies',
                           remote_side=[parent_id])
    
    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.content:
            service = MarkdownService()
            result = service.convert(self.content)
            self.html_content = result['html']
    
    def __repr__(self):
        return f'<Comment {self.id}>' 