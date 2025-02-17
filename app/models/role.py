"""
文件名：role.py
描述：角色数据模型
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime, UTC
from app.extensions import db
import json

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))
    _permissions = db.Column('permissions', db.Text, default='[]')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    # 关联关系
    users = db.relationship('User', back_populates='role', lazy='dynamic')
    
    @property
    def permissions(self):
        """获取权限列表"""
        return json.loads(self._permissions)
    
    @permissions.setter
    def permissions(self, value):
        """设置权限列表"""
        self._permissions = json.dumps(value)
    
    def has_permission(self, permission):
        """检查是否有指定权限"""
        return permission in self.permissions
    
    def add_permission(self, permission):
        """添加权限"""
        if not self.has_permission(permission):
            perms = self.permissions
            perms.append(permission)
            self.permissions = perms
    
    def remove_permission(self, permission):
        """移除权限"""
        if self.has_permission(permission):
            perms = self.permissions
            perms.remove(permission)
            self.permissions = perms
    
    def reset_permissions(self):
        """重置所有权限"""
        self.permissions = []
    
    def __repr__(self):
        return f'<Role {self.name}>' 