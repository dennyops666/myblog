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

# 用户角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    extend_existing=True
)

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    _password = db.Column('password', db.String(128), nullable=False)
    nickname = db.Column(db.String(64))
    avatar = db.Column(db.String(200))
    bio = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    
    # 关系
    roles = db.relationship('Role', secondary=user_roles, lazy='subquery',
                          back_populates='users')
    posts = db.relationship('Post', backref='author', lazy=True,
                          cascade='all, delete-orphan')
    comments = db.relationship('Comment', back_populates='author', lazy='dynamic',
                             cascade='all, delete-orphan',
                             foreign_keys='Comment.author_id')
    
    @property
    def password(self):
        """密码属性"""
        raise AttributeError('密码不可读')
    
    @password.setter
    def password(self, password):
        """设置密码"""
        self._password = generate_password_hash(password)
    
    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self._password, password)
        
    def check_password(self, password):
        """验证密码（别名方法）"""
        return self.verify_password(password)
        
    def set_password(self, password):
        """设置密码"""
        self.password = password
        
    def has_role(self, role_name):
        """检查用户是否有指定角色"""
        return any(role.name == role_name for role in self.roles)
        
    def add_role(self, role):
        """添加角色"""
        if not self.has_role(role.name):
            self.roles.append(role)
            
    def remove_role(self, role):
        """移除角色"""
        if self.has_role(role.name):
            self.roles.remove(role)
            
    def activate(self):
        """激活用户"""
        self.is_active = True
        db.session.commit()
        
    def deactivate(self):
        """停用用户"""
        self.is_active = False
        db.session.commit()
            
    def __repr__(self):
        return f'<User {self.username}>'