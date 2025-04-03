"""
文件名：setting_fix.py
描述：修复后的站点设置模型
作者：denny
"""

from app.extensions import db
from datetime import datetime

class Setting(db.Model):
    """站点设置模型"""
    __tablename__ = 'settings'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255))
    # 直接列
    blog_name = db.Column(db.String(100))
    blog_description = db.Column(db.Text)
    posts_per_page = db.Column(db.Integer)
    allow_registration = db.Column(db.Boolean)
    allow_comments = db.Column(db.Boolean)
    
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __init__(self, key, value, description=None, blog_name=None, blog_description=None, 
                 posts_per_page=None, allow_registration=None, allow_comments=None):
        self.key = key
        self.value = value
        self.description = description or key
        # 同时设置直接列
        if key == 'site_name' and blog_name is None:
            self.blog_name = value
        elif blog_name is not None:
            self.blog_name = blog_name
            
        if key == 'site_description' and blog_description is None:
            self.blog_description = value
        elif blog_description is not None:
            self.blog_description = blog_description
            
        if key == 'posts_per_page' and posts_per_page is None:
            try:
                self.posts_per_page = int(value)
            except (ValueError, TypeError):
                self.posts_per_page = 10
        elif posts_per_page is not None:
            self.posts_per_page = posts_per_page
            
        if key == 'allow_registration' and allow_registration is None:
            self.allow_registration = (value.lower() == 'true') if isinstance(value, str) else bool(value)
        elif allow_registration is not None:
            self.allow_registration = allow_registration
            
        if key == 'enable_comments' and allow_comments is None:
            self.allow_comments = (value.lower() == 'true') if isinstance(value, str) else bool(value)
        elif allow_comments is not None:
            self.allow_comments = allow_comments
    
    def __repr__(self):
        return f'<Setting {self.key}>'
