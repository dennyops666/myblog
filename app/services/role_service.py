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
    
    def get_available_roles(self, user=None):
        """获取可用的角色列表
        
        如果当前用户不是超级管理员，则超级管理员角色将被排除
        
        Args:
            user: 当前用户对象，如果为None则从flask_login获取
            
        Returns:
            list: 可用的角色列表
        """
        try:
            # 如果没有传入user参数，则从flask_login获取
            if user is None:
                try:
                    from flask_login import current_user
                    user = current_user
                except Exception as e:
                    current_app.logger.error(f'获取当前用户失败: {str(e)}')
                    return []
            
            # 默认排除超级管理员角色
            exclude_roles = ['super_admin']
            
            # 如果当前用户是超级管理员，则可以看到所有角色
            if hasattr(user, 'is_super_admin') and user.is_super_admin:
                roles = Role.query.order_by(Role.id).all()
            else:
                # 非超级管理员用户看不到超级管理员角色
                roles = Role.query.filter(Role.name.notin_(exclude_roles)).order_by(Role.id).all()
            
            return roles
        except Exception as e:
            current_app.logger.error(f'获取角色列表失败: {str(e)}')
            return []
            
    def get_roles_by_ids(self, role_ids):
        """根据ID列表获取角色
        
        Args:
            role_ids: 角色ID列表
            
        Returns:
            list: 角色列表
        """
        return Role.query.filter(Role.id.in_(role_ids)).all()
    
    def get_role_by_name(self, name):
        """根据名称获取角色"""
        try:
            return Role.query.filter_by(name=name).first()
        except Exception as e:
            current_app.logger.error(f'获取角色失败: {str(e)}')
            return None
            
    def get_role_by_id(self, role_id):
        """根据ID获取角色"""
        try:
            return Role.query.get(role_id)
        except Exception as e:
            current_app.logger.error(f'获取角色失败: {str(e)}')
            return None 