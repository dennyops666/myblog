"""
文件名：notification.py
描述：通知服务
作者：denny
创建日期：2024-03-21
"""

from app.models import User, Comment, Post, db
from app.models.notification import Notification
from datetime import datetime, UTC

class NotificationService:
    def __init__(self):
        pass

    def notify_new_comment(self, comment):
        """通知文章作者有新评论"""
        if not comment or not comment.post:
            return False
            
        post = comment.post
        author = post.author
        
        if not author:
            return False
            
        notification = Notification(
            user_id=author.id,
            content=f'您的文章《{post.title}》收到了新评论',
            type='comment',
            target_id=comment.id
        )
        db.session.add(notification)
        db.session.commit()
        return True

    def notify_comment_reply(self, comment):
        """通知评论作者有新回复"""
        if not comment or not comment.parent:
            return False
            
        parent_comment = comment.parent
        parent_author = parent_comment.author
        
        if not parent_author:
            return False
            
        notification = Notification(
            user_id=parent_author.id,
            content=f'您的评论收到了新回复',
            type='reply',
            target_id=comment.id
        )
        db.session.add(notification)
        db.session.commit()
        return True
        
    @staticmethod
    def get_user_notifications(user_id, include_read=False):
        """获取用户的通知列表
        
        参数：
            user_id (int): 用户ID
            include_read (bool): 是否包含已读通知
            
        返回：
            list: 通知列表
        """
        query = Notification.query.filter_by(user_id=user_id)
        if not include_read:
            query = query.filter_by(read=False)
        return query.order_by(Notification.created_at.desc()).all()
        
    @staticmethod
    def mark_as_read(notification_id):
        """将通知标记为已读"""
        notification = db.session.get(Notification, notification_id)
        if notification:
            notification.read = True
            db.session.commit()
            return True
        return False
        
    @staticmethod
    def mark_all_as_read(user_id):
        """将用户的所有通知标记为已读"""
        Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
        db.session.commit() 