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
    __table_args__ = {'extend_existing': True}
    
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
    author = db.relationship('User', back_populates='comments',
                           foreign_keys=[author_id])
    
    # 自引用关系
    replies = db.relationship('Comment',
                            backref=db.backref('parent', remote_side=[id]),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(Comment, self).__init__(**kwargs)
        if self.content:
            service = MarkdownService()
            result = service.convert(self.content)
            self.html_content = result['html']
    
    @property
    def author_name(self):
        """获取评论作者名称"""
        if self.author:
            return self.author.username
        return self.nickname or '匿名用户'
    
    @author_name.setter
    def author_name(self, value):
        """设置评论作者名称"""
        self.nickname = value
    
    @property
    def author_email(self):
        """获取评论作者邮箱"""
        if self.author:
            return self.author.email
        return self.email or ''
    
    @author_email.setter
    def author_email(self, value):
        """设置评论作者邮箱"""
        self.email = value
    
    @property
    def is_approved(self):
        """评论是否已审核通过"""
        return self.status == 1
    
    @property
    def has_replies(self):
        """是否有回复"""
        return self.replies.count() > 0
    
    @property
    def reply_count(self):
        """获取回复数量"""
        return self.replies.count()
    
    def approve(self):
        """审核通过评论"""
        self.status = 1
        db.session.commit()
    
    def reject(self):
        """拒绝评论"""
        db.session.delete(self)
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id}>' 