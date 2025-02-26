"""
文件名：role.py
描述：角色模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC
from app.models.permission import Permission

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    permissions = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    def has_permission(self, permission):
        """检查是否有指定权限"""
        return self.permissions & permission == permission
    
    def add_permission(self, permission):
        """添加权限"""
        if not self.has_permission(permission):
            self.permissions += permission
    
    def remove_permission(self, permission):
        """移除权限"""
        if self.has_permission(permission):
            self.permissions -= permission
    
    def reset_permissions(self):
        """重置权限"""
        self.permissions = 0
    
    @staticmethod
    def insert_roles():
        """插入默认角色"""
        roles = {
            'viewer': Permission.VIEWER,
            'user': Permission.USER,
            'editor': Permission.EDITOR,
            'moderator': Permission.MODERATOR,
            'admin': Permission.ADMINISTRATOR
        }
        
        for name, permissions in roles.items():
            role = Role.query.filter_by(name=name).first()
            if role is None:
                role = Role(name=name, permissions=permissions)
                db.session.add(role)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Role {self.name}>'