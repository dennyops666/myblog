from datetime import datetime, timedelta
from sqlalchemy import and_, desc, func
from app.extensions import db

NOTIFICATION_TYPES = {
    'comment': '新评论',
    'reply': '回复评论',
    'system': '系统通知'
}

class Notification(db.Model):
    __tablename__ = 'notifications'

    # 主键和外键
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 通知内容
    content = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(50), nullable=False, index=True)
    target_id = db.Column(db.Integer, index=True)
    
    # 状态字段
    read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # 关系
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))

    # 复合索引
    __table_args__ = (
        db.Index('idx_user_type', user_id, type),
        db.Index('idx_user_read', user_id, read),
        db.Index('idx_user_created', user_id, created_at.desc())
    )

    @property
    def type_display(self):
        return NOTIFICATION_TYPES.get(self.type, self.type)
    
    @property
    def is_recent(self):
        return (datetime.utcnow() - self.created_at) <= timedelta(days=7)
    
    @classmethod
    def get_unread_count(cls, user_id):
        return cls.query.filter_by(user_id=user_id, read=False).count()
    
    @classmethod
    def get_user_notifications(cls, user_id, search=None, limit=None, include_read=True):
        query = cls.query.filter_by(user_id=user_id)
        
        if not include_read:
            query = query.filter_by(read=False)
        
        if search:
            query = query.filter(cls.content.ilike(f'%{search}%'))
        
        query = query.order_by(desc(cls.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def get_notifications_by_type(cls, user_id, type, limit=None):
        query = cls.query.filter_by(user_id=user_id, type=type)
        return cls._apply_common_filters(query, limit=limit)
    
    @classmethod
    def get_recent_notifications(cls, user_id, days=7):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= cutoff_date
        )
        return cls._apply_common_filters(query)
    
    @classmethod
    def get_notification_stats(cls, user_id):
        stats = db.session.query(
            cls.type,
            func.count(cls.id).label('total'),
            func.sum(cls.read == False).label('unread')
        ).filter_by(user_id=user_id)\
         .group_by(cls.type).all()
        
        result = {
            type: {'total': total, 'unread': unread or 0}
            for type, total, unread in stats
        }
        
        # 确保所有通知类型都有统计数据
        for type in NOTIFICATION_TYPES:
            if type not in result:
                result[type] = {'total': 0, 'unread': 0}
        
        return result
    
    @classmethod
    def get_notifications_by_target(cls, user_id, target_id):
        query = cls.query.filter_by(user_id=user_id, target_id=target_id)
        return cls._apply_common_filters(query)
    
    @classmethod
    def get_notifications_by_date_range(cls, user_id, start_date, end_date):
        query = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= start_date,
            cls.created_at <= end_date
        )
        return cls._apply_common_filters(query)
    
    @classmethod
    def _apply_common_filters(cls, query, limit=None):
        query = query.order_by(desc(cls.created_at))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @classmethod
    def mark_as_read(cls, notification_ids, user_id):
        notifications = cls.query.filter(
            and_(
                cls.id.in_(notification_ids),
                cls.user_id == user_id,
                cls.read == False
            )
        ).all()
        
        for notification in notifications:
            notification.read = True
        
        return len(notifications)
    
    @classmethod
    def mark_all_as_read(cls, user_id):
        return cls.query.filter_by(
            user_id=user_id,
            read=False
        ).update({'read': True})
    
    @classmethod
    def clear_read_notifications(cls, user_id):
        return cls.query.filter_by(
            user_id=user_id,
            read=True
        ).delete()
    
    @classmethod
    def clear_old_notifications(cls, user_id, days=30):
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(
            cls.user_id == user_id,
            cls.created_at < cutoff_date,
            cls.read == True
        ).delete()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'type': self.type,
            'type_display': self.type_display,
            'target_id': self.target_id,
            'read': self.read,
            'created_at': self.created_at.isoformat(),
            'is_recent': self.is_recent
        }
    
    def validate_type(self):
        if self.type not in NOTIFICATION_TYPES:
            raise ValueError(f'无效的通知类型: {self.type}')
    
    def validate_content(self):
        if not self.content:
            raise ValueError('通知内容不能为空')
        
        if len(self.content) > 500:
            raise ValueError('通知内容不能超过500个字符')
    
    def validate(self):
        self.validate_type()
        self.validate_content()
    
    def mark_as_read(self):
        if not self.read:
            self.read = True
            return True
        return False
    
    def mark_as_unread(self):
        if self.read:
            self.read = False
            return True
        return False
    
    @classmethod
    def create_notification(cls, user_id, content, type, target_id=None):
        notification = cls(user_id=user_id, content=content, type=type, target_id=target_id)
        notification.validate()
        return notification