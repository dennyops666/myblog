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
    role = db.Column(db.Integer, default=0)  # 0: 普通用户, 1: 管理员
    status = db.Column(db.Integer, default=1)  # 0: 禁用, 1: 正常
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    
    @property
    def password(self):
        """密码属性不可读"""
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        """设置密码时自动进行哈希"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password):
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 