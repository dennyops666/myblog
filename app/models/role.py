"""
文件名：role.py
描述：角色模型
作者：denny
创建日期：2024-03-21
"""

from app.extensions import db
from datetime import datetime, UTC
from app.models.permission import Permission

# 用户角色关联表
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    extend_existing=True
)

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    __table_args__ = {'extend_existing': True}
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    permissions = db.Column(db.Integer, default=Permission.NONE.value)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC),
                          onupdate=lambda: datetime.now(UTC))
    
    # 关系
    users = db.relationship('User', secondary=user_roles,
                          back_populates='roles', lazy='dynamic')
    
    def __init__(self, name, description=None, permissions=Permission.NONE):
        """初始化角色"""
        self.name = name
        self.description = description
        self.permissions = permissions.value if isinstance(permissions, Permission) else permissions
    
    def has_permission(self, permission):
        """检查是否具有指定权限"""
        return bool(self.permissions & permission.value if isinstance(permission, Permission) else permission)
    
    def add_permission(self, permission):
        """添加权限"""
        if not self.has_permission(permission):
            self.permissions |= permission.value if isinstance(permission, Permission) else permission
    
    def remove_permission(self, permission):
        """移除权限"""
        if self.has_permission(permission):
            self.permissions &= ~(permission.value if isinstance(permission, Permission) else permission)
    
    def reset_permissions(self):
        """重置权限"""
        self.permissions = Permission.NONE.value
    
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