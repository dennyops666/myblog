"""
文件名：session.py
描述：会话模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
import secrets

class Session(db.Model):
    """会话模型"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.String(128), unique=True, nullable=False)
    csrf_token = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime, nullable=False)
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic'))
    
    def __init__(self, user_id, expires_at, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.session_id = secrets.token_urlsafe(32)
        self.csrf_token = secrets.token_urlsafe(32)
        self.expires_at = expires_at
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    def is_expired(self):
        """检查会话是否过期"""
        return datetime.now(UTC) > self.expires_at
    
    def is_valid(self, ip_address=None, user_agent=None):
        """检查会话是否有效
        
        Args:
            ip_address: 客户端IP地址
            user_agent: 客户端用户代理
            
        Returns:
            bool: 会话是否有效
        """
        if not self.is_active:
            return False
            
        if self.is_expired():
            return False
            
        if ip_address and self.ip_address != ip_address:
            return False
            
        if user_agent and self.user_agent != user_agent:
            return False
            
        return True
    
    def update_activity(self):
        """更新最后活动时间"""
        self.last_active = datetime.now(UTC)
        db.session.commit()
    
    def invalidate(self):
        """使会话失效"""
        self.is_active = False
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """清理过期会话"""
        cls.query.filter(
            (cls.expires_at < datetime.now(UTC)) |
            (cls.is_active == False)  # noqa: E712
        ).delete()
        db.session.commit()
    
    def __repr__(self):
        return f'<Session {self.id}>'