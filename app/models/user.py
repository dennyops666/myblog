"""
文件名：user.py
描述：用户数据模型
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
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
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    # 关系
    role = db.relationship('Role', back_populates='users')
    posts = db.relationship('Post', back_populates='author', lazy='dynamic')
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    last_login = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role_id is None:
            from app.models import Role
            user_role = Role.query.filter_by(name='user').first()
            if user_role:
                self.role_id = user_role.id
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def verify_password(self, password):
        """验证密码（别名方法）"""
        return self.check_password(password)
    
    def is_admin(self):
        """检查是否是管理员"""
        return self.role and self.role.name == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id)) 