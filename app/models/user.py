"""
文件名：user.py
描述：用户模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, UTC

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    
    # 关系
    roles = db.relationship('Role', secondary='user_roles', back_populates='users')
    posts = db.relationship('Post', back_populates='author', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic',
                             foreign_keys='Comment.author_id')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
        
    def has_role(self, role_name):
        """检查是否有指定角色"""
        return any(role.name == role_name for role in self.roles)
        
    def add_role(self, role):
        """添加角色"""
        if not self.has_role(role.name):
            self.roles.append(role)
            
    def remove_role(self, role):
        """移除角色"""
        if self.has_role(role.name):
            self.roles.remove(role)
            
    def __repr__(self):
        return f'<User {self.username}>'