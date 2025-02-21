"""
文件名：role.py
描述：角色模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC

# 用户角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=lambda: datetime.now(UTC))
)

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    
    # 关系
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    
    def __init__(self, name, description=None):
        """初始化角色"""
        self.name = name
        self.description = description
        
    def __repr__(self):
        """字符串表示"""
        return f'<Role {self.name}>'