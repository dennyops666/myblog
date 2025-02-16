"""
文件名：comment.py
描述：评论数据模型
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime
from app import db

class Comment(db.Model):
    """评论模型"""
    __tablename__ = 'comments'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    html_content = db.Column(db.Text)  # 存储解析后的HTML内容
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 添加作者ID字段
    author_name = db.Column(db.String(50), nullable=False)
    author_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0: 待审核, 1: 已通过
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关联关系
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic')
    author = db.relationship('User', foreign_keys=[author_id])  # 修改作者关联定义
    
    def __repr__(self):
        return f'<Comment {self.id}>' 