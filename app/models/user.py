"""
文件名：user.py
描述：用户数据模型
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from app import db, login_manager

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # 角色关联
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    # 关系
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', foreign_keys='Comment.author_id', backref='user', lazy='dynamic')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            # 如果没有指定角色，默认设置为普通用户
            from app.models import Role
            user_role = Role.query.filter_by(name='user').first()
            if user_role:
                self.role = user_role
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def can(self, permission):
        """检查用户是否有指定权限"""
        return self.role is not None and self.role.has_permission(permission)
    
    def is_administrator(self):
        """检查用户是否是管理员"""
        return self.role is not None and self.role.name == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 