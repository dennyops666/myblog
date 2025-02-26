"""
文件名：role_service.py
描述：角色服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.extensions import db
from app.models.role import Role
from app.models.permission import Permission

class RoleService:
    """角色服务类"""
    
    def create_role(self, name, description=None, permissions=0):
        """创建角色
        
        Args:
            name: 角色名称
            description: 角色描述
            permissions: 权限值
            
        Returns:
            dict: 包含状态和消息的字典
            
        Raises:
            ValueError: 如果角色名已存在
        """
        if Role.query.filter_by(name=name).first():
            raise ValueError('角色名已存在')
            
        role = Role(
            name=name,
            description=description,
            permissions=permissions
        )
        
        db.session.add(role)
        db.session.commit()
        
        return {'status': 'success', 'message': '角色创建成功', 'role': role}
    
    def update_role(self, role_id, name=None, description=None, permissions=None):
        """更新角色
        
        Args:
            role_id: 角色ID
            name: 新角色名
            description: 新描述
            permissions: 新权限值
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            role = db.session.get(Role, role_id)
            if not role:
                return {'status': 'error', 'message': '角色不存在'}
                
            if name and name != role.name:
                if Role.query.filter_by(name=name).first():
                    return {'status': 'error', 'message': '角色名已存在'}
                role.name = name
                
            if description is not None:
                role.description = description
                
            if permissions is not None:
                role.permissions = permissions
                
            role.updated_at = datetime.now(UTC)
            db.session.commit()
            
            return {'status': 'success', 'message': '角色更新成功', 'role': role}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新角色失败: {str(e)}")
            return {'status': 'error', 'message': '更新角色失败，请稍后重试'}
    
    def delete_role(self, role_id):
        """删除角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            role = db.session.get(Role, role_id)
            if not role:
                return {'status': 'error', 'message': '角色不存在'}
                
            db.session.delete(role)
            db.session.commit()
            
            return {'status': 'success', 'message': '角色删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除角色失败: {str(e)}")
            return {'status': 'error', 'message': '删除角色失败，请稍后重试'}
    
    def get_role(self, role_id):
        """获取角色
        
        Args:
            role_id: 角色ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            role = db.session.get(Role, role_id)
            if not role:
                return {'status': 'error', 'message': '角色不存在'}
                
            return {'status': 'success', 'role': role}
            
        except Exception as e:
            current_app.logger.error(f"获取角色失败: {str(e)}")
            return {'status': 'error', 'message': '获取角色失败，请稍后重试'}
    
    def get_all_roles(self):
        """获取所有角色
        
        Returns:
            list: 角色列表
        """
        return Role.query.all()
    
    def get_available_roles(self):
        """获取可用角色（不包括超级管理员）"""
        return Role.query.filter(~Role.permissions.op('&')(Permission.SUPER_ADMIN.value)).all()
    
    def get_roles_by_ids(self, role_ids):
        """根据ID列表获取角色
        
        Args:
            role_ids: 角色ID列表
            
        Returns:
            list: 角色列表
        """
        return Role.query.filter(Role.id.in_(role_ids)).all()
    
    def get_role_by_name(self, name):
        """根据名称获取角色
        
        Args:
            name: 角色名称
            
        Returns:
            Role: 角色对象
        """
        return Role.query.filter_by(name=name).first() 