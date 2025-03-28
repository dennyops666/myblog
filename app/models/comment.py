"""
文件名：comment.py
描述：评论数据模型
作者：denny
"""

from datetime import datetime, UTC
from app.extensions import db
from app.utils.markdown import markdown_to_html
from enum import IntEnum
from sqlalchemy import event
from flask_login import current_user

class CommentStatus(IntEnum):
    """评论状态枚举"""
    PENDING = 0  # 待审核
    APPROVED = 1  # 已通过
    REJECTED = 2  # 已拒绝

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
    email = db.Column(db.String(100))  # 匿名评论者的邮箱
    status = db.Column(db.Integer, default=CommentStatus.APPROVED)  # 评论状态，默认为已审核，改变默认值
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    # 关系
    post = db.relationship('Post', back_populates='comments')
    author = db.relationship('User', back_populates='comments', foreign_keys=[author_id])
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), 
                             cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """初始化评论对象
        
        如果提供了content参数，则自动将Markdown内容转换为HTML并设置html_content
        已登录用户的评论默认设置为审核通过
        """
        super(Comment, self).__init__(**kwargs)
        
        from app.utils.markdown import markdown_to_html
        
        # 设置HTML内容
        if self.content and (self.html_content is None or self.html_content == ''):
            self.html_content = markdown_to_html(self.content)
            
        # 如果评论状态为待审核且作者已登录，则自动设置为已审核
        if self.status == CommentStatus.PENDING and self.author_id is not None:
            self.status = CommentStatus.APPROVED
            current_app.logger.info(f"已登录用户评论自动设置为已审核: author_id={self.author_id}, status={self.status}")
    
    @property
    def author_name(self):
        """获取评论作者名称"""
        return self.author.username if self.author else self.nickname
    
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
        return self.status == CommentStatus.APPROVED
    
    @property
    def has_replies(self):
        """是否有回复"""
        return self.replies.count() > 0
    
    @property
    def reply_count(self):
        """获取回复数量"""
        return self.replies.count()
    
    @property
    def is_from_authenticated_user(self):
        """判断评论是否来自已认证用户"""
        return self.author_id is not None
    
    def ensure_correct_status(self):
        """确保评论状态正确
        所有评论都应该为已审核状态
        """
        if self.status != CommentStatus.APPROVED:
            self.status = CommentStatus.APPROVED
            return True
        return False
    
    def approve(self):
        """审核通过评论"""
        self.status = CommentStatus.APPROVED
        db.session.commit()
    
    def reject(self):
        """拒绝评论"""
        self.status = CommentStatus.REJECTED
        db.session.commit()
    
    def __repr__(self):
        return f'<Comment {self.id}>'
        
    def to_dict(self):
        """转换评论对象为字典"""
        return {
            'id': self.id,
            'content': self.content,
            'html_content': self.html_content,
            'post_id': self.post_id,
            'parent_id': self.parent_id,
            'author_name': self.author_name,
            'author_email': self.author_email,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        } 

# 添加数据库事件监听器
@event.listens_for(Comment, 'before_insert')
def before_insert_comment(mapper, connection, comment):
    """在评论插入数据库前触发的事件"""
    from flask import current_app
    
    # 对于待审核状态的评论，将其更改为已审核状态
    if comment.status == CommentStatus.PENDING:
        comment.status = CommentStatus.APPROVED
        current_app.logger.info(f"事件监听器: 评论 before_insert, 将待审核状态更改为已审核, id={comment.id}")

@event.listens_for(Comment, 'after_insert')
def after_insert_comment(mapper, connection, comment):
    """在评论插入数据库后触发的事件"""
    from flask import current_app
    
    # 对于待审核状态的评论，将其更改为已审核状态
    if comment.status == CommentStatus.PENDING:
        # 使用 UPDATE 语句直接更新数据库中的记录
        connection.execute(
            db.text("UPDATE comments SET status = :status WHERE id = :id"),
            {"status": int(CommentStatus.APPROVED), "id": comment.id}
        )
        current_app.logger.warning(f"事件监听器: 评论 after_insert, 将待审核状态更改为已审核, id={comment.id}")

# 评论保存前检查评论状态
@event.listens_for(Comment, 'before_insert')
def set_comment_status_on_insert(mapper, connection, comment):
    """确保新创建的评论状态为已审核，但不修改已拒绝的评论"""
    from flask import current_app
    # 对于待审核状态的评论，设置为已审核状态
    if comment.status == CommentStatus.PENDING:
        current_app.logger.info(f"【评论审核-模型事件】将待审核评论状态更改为已审核: id={comment.id}")
        comment.status = CommentStatus.APPROVED

@event.listens_for(Comment, 'before_update')
def set_comment_status_on_update(mapper, connection, comment):
    """确保更新的评论状态为已审核，但不修改已拒绝的评论"""
    from flask import current_app
    # 对于待审核状态的评论，设置为已审核状态
    if comment.status == CommentStatus.PENDING:
        current_app.logger.info(f"【评论审核-模型事件】更新评论时将待审核状态更改为已审核: comment_id={comment.id}")
        comment.status = CommentStatus.APPROVED

# 添加插入后监听器，确保评论状态正确
@event.listens_for(Comment, 'after_insert')
def ensure_comment_status_after_insert(mapper, connection, comment):
    """在评论插入后确保评论状态正确"""
    from flask import current_app
    # 对于待审核状态的评论，设置为已审核状态
    if comment.status == CommentStatus.PENDING:
        # 直接执行SQL更新
        current_app.logger.warning(f"【评论审核-模型事件】插入后将待审核评论状态更改为已审核: comment_id={comment.id}")
        connection.execute(
            db.text("UPDATE comments SET status = :status WHERE id = :id"),
            {"status": int(CommentStatus.APPROVED), "id": comment.id}
        )

# 添加更新后监听器，确保评论状态正确
@event.listens_for(Comment, 'after_update')
def ensure_comment_status_after_update(mapper, connection, comment):
    """在评论更新后确保评论状态正确"""
    from flask import current_app
    # 对于待审核状态的评论，设置为已审核状态
    if comment.status == CommentStatus.PENDING:
        # 直接执行SQL更新
        current_app.logger.warning(f"【评论审核-模型事件】更新后将待审核评论状态更改为已审核: comment_id={comment.id}")
        connection.execute(
            db.text("UPDATE comments SET status = :status WHERE id = :id"),
            {"status": int(CommentStatus.APPROVED), "id": comment.id}
        )

# 添加 SQLAlchemy 加载后监听器，确保所有评论状态为已审核
@event.listens_for(Comment, 'load')
def ensure_status_on_load(target, context):
    """当评论从数据库加载时，确保评论状态为已审核"""
    from flask import current_app
    try:
        # 对于状态为待审核的评论，将其更改为已审核状态
        if target.status == CommentStatus.PENDING:
            # 记录状态变化
            old_status = target.status
            # 设置状态为已审核
            target.status = CommentStatus.APPROVED
            current_app.logger.warning(f"【评论审核-加载事件】将待审核评论状态更改为已审核: id={target.id}, old_status={old_status}")
        # 保留已拒绝状态的评论状态
    except Exception as e:
        current_app.logger.error(f"【评论审核-加载事件】修正评论状态失败: {str(e)}")

# 添加服务器启动时的评论状态修正函数
def fix_comment_status_on_startup():
    """在应用启动时修正评论状态"""
    from flask import current_app
    from app.extensions import db
    try:
        # 更新所有待审核的评论为已审核状态，保留已拒绝的评论状态
        result = db.session.execute(
            db.text("UPDATE comments SET status = :approved WHERE status = :pending"),
            {"approved": int(CommentStatus.APPROVED), "pending": int(CommentStatus.PENDING)}
        )
        affected_rows = result.rowcount
        db.session.commit()
        
        if affected_rows > 0:
            current_app.logger.info(f"【评论审核-启动修正】将 {affected_rows} 条待审核评论修改为已审核状态")
        return affected_rows
    except Exception as e:
        current_app.logger.error(f"【评论审核-启动修正】修正评论状态失败: {str(e)}")
        db.session.rollback()
        return 0 