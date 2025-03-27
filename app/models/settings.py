"""
文件名：settings.py
描述：系统设置模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC

class Settings(db.Model):
    """系统设置模型"""
    __tablename__ = 'settings'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    blog_name = db.Column(db.String(100), default='MyBlog')
    blog_description = db.Column(db.Text, nullable=True)
    posts_per_page = db.Column(db.Integer, default=10)
    allow_registration = db.Column(db.Boolean, default=True)
    allow_comments = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)) 