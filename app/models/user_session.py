"""
文件名：user_session.py
描述：用户会话模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, timedelta, UTC
from app.extensions import db

class UserSession(db.Model):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(200))
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # 关联用户
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    def __init__(self, **kwargs):
        super(UserSession, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.now(UTC) + timedelta(days=30)
    
    @property
    def is_expired(self):
        """检查会话是否过期"""
        return datetime.now(UTC) > self.expires_at
    
    def refresh(self):
        """刷新会话"""
        self.last_activity = datetime.now(UTC)
        self.expires_at = datetime.now(UTC) + timedelta(days=30)
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>' 