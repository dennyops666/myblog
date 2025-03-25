from app.models.notification import Notification

class NotificationService:
    def create_notification(self, user_id, content, type, target_id=None):
        if type not in ('comment', 'reply', 'system'):
            return None
            
        return Notification(
            user_id=user_id,
            content=content,
            type=type,
            target_id=target_id
        )

    def notify_new_comment(self, comment):
        if not comment or not comment.post or not comment.post.author:
            return None
            
        return self.create_notification(
            user_id=comment.post.author.id,
            content=f'您的文章《{comment.post.title}》收到了新评论',
            type='comment',
            target_id=comment.id
        )

    def notify_comment_reply(self, comment):
        if not comment or not comment.parent or not comment.parent.author:
            return None
            
        return self.create_notification(
            user_id=comment.parent.author.id,
            content=f'您的评论收到了新回复',
            type='reply',
            target_id=comment.id
        )
    
    def notify_system(self, user_id, content):
        return self.create_notification(
            user_id=user_id,
            content=content,
            type='system'
        )
    
    def get_notifications(self, user_id=None, search=None, limit=None, include_read=True):
        query = Notification.query
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if not include_read:
            query = query.filter_by(read=False)
        
        if search:
            query = query.filter(Notification.content.ilike(f'%{search}%'))
        
        query = query.order_by(Notification.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_unread_count(self, user_id):
        return Notification.query.filter_by(user_id=user_id, read=False).count()
    
    def get_notification_by_id(self, notification_id):
        return Notification.query.get(notification_id)