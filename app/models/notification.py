from datetime import datetime, UTC
from app.extensions import db

class Notification(db.Model):
    """通知模型"""
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 通知类型：comment, reply, system等
    target_id = db.Column(db.Integer)  # 目标ID（如评论ID、文章ID等）
    read = db.Column(db.Boolean, default=False)  # 是否已读
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))

    # 关联
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id}>' 