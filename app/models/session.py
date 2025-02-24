"""
文件名：session.py
描述：会话模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from app.extensions import db
import secrets
import json

class UserSession(db.Model):
    """用户会话模型"""
    __tablename__ = 'user_sessions'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    data = db.Column(db.Text)  # Flask-Session 数据
    expiry = db.Column(db.DateTime, nullable=False)  # Flask-Session 过期时间
    
    # 用户会话相关字段
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    csrf_token = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    last_active = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    is_active = db.Column(db.Boolean, default=True)
    
    user = db.relationship('User', backref=db.backref('user_sessions', lazy='dynamic'))
    
    def __init__(self, session_id, data=None, expiry=None, user_id=None, 
                 ip_address=None, user_agent=None):
        self.session_id = session_id
        self.data = json.dumps(data) if isinstance(data, dict) else data
        self.expiry = expiry
        self.user_id = user_id
        self.csrf_token = secrets.token_urlsafe(32)
        self.ip_address = ip_address
        self.user_agent = user_agent
    
    @property
    def serialized_data(self):
        """获取序列化的数据"""
        if self.data:
            try:
                return json.loads(self.data)
            except:
                return {}
        return {}
    
    @serialized_data.setter
    def serialized_data(self, value):
        """设置序列化的数据"""
        self.data = json.dumps(value) if value else '{}'
    
    def is_expired(self):
        """检查会话是否过期"""
        return datetime.now(UTC) > self.expiry
    
    def is_valid(self, ip_address=None, user_agent=None):
        """检查会话是否有效"""
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
            (cls.expiry < datetime.now(UTC)) |
            (cls.is_active == False)  # noqa: E712
        ).delete()
        db.session.commit()
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'