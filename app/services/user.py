"""
文件名：user.py
描述：用户服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from app.services.security import SecurityService

class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.security_service = SecurityService()
        
    def get_user_by_id(self, user_id):
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            User: 用户对象
        """
        return User.query.get(user_id)
        
    def get_user_by_username(self, username):
        """根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            User: 用户对象
        """
        return User.query.filter_by(username=username).first()
        
    def get_user_by_email(self, email):
        """根据邮箱获取用户
        
        Args:
            email: 邮箱
            
        Returns:
            User: 用户对象
        """
        return User.query.filter_by(email=email).first()
        
    def update_user(self, user_id, data):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            data: 要更新的数据
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            # 清理输入
            if 'username' in data:
                data['username'] = self.security_service.sanitize_input(data['username'])
            if 'email' in data:
                data['email'] = self.security_service.sanitize_input(data['email'])
            if 'bio' in data:
                data['bio'] = self.security_service.sanitize_input(data['bio'])
                
            # 检查用户名是否已存在
            if 'username' in data and data['username'] != user.username:
                if User.query.filter_by(username=data['username']).first():
                    return {'status': 'error', 'message': '用户名已存在'}
                    
            # 检查邮箱是否已存在
            if 'email' in data and data['email'] != user.email:
                if User.query.filter_by(email=data['email']).first():
                    return {'status': 'error', 'message': '邮箱已被注册'}
                    
            # 更新角色
            if 'role' in data:
                role = Role.query.filter_by(name=data['role']).first()
                if role:
                    user.roles = [role]
                    
            # 更新其他字段
            for key, value in data.items():
                if hasattr(user, key) and key not in ['id', 'password_hash', 'roles']:
                    setattr(user, key, value)
                    
            user.updated_at = datetime.now(UTC)
            db.session.commit()
            
            return {'status': 'success', 'message': '用户信息更新成功', 'user': user}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户信息失败: {str(e)}")
            return {'status': 'error', 'message': '更新用户信息失败，请稍后重试'}
            
    def delete_user(self, user_id):
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            db.session.delete(user)
            db.session.commit()
            
            return {'status': 'success', 'message': '用户删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除用户失败: {str(e)}")
            return {'status': 'error', 'message': '删除用户失败，请稍后重试'}
            
    def get_users(self, page=1, per_page=10, role=None):
        """获取用户列表
        
        Args:
            page: 页码
            per_page: 每页数量
            role: 角色名
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            query = User.query
            
            # 按角色筛选
            if role:
                query = query.join(User.roles).filter(Role.name == role)
                
            # 分页
            pagination = query.order_by(User.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'status': 'success',
                'users': pagination.items,
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': pagination.page
            }
            
        except Exception as e:
            current_app.logger.error(f"获取用户列表失败: {str(e)}")
            return {'status': 'error', 'message': '获取用户列表失败，请稍后重试'}
    
    def update_profile(self, user, data):
        """更新用户资料"""
        try:
            for key, value in data.items():
                if hasattr(user, key) and key not in ['id', 'password_hash']:
                    setattr(user, key, value)
            db.session.commit()
            return True, "资料更新成功"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户资料失败: {str(e)}")
            return False, "资料更新失败，请稍后重试"
    
    def update_avatar(self, user, avatar_url):
        """更新用户头像"""
        try:
            user.avatar = avatar_url
            db.session.commit()
            return True, "头像更新成功"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户头像失败: {str(e)}")
            return False, "头像更新失败，请稍后重试"
    
    def change_role(self, user, role_name):
        """修改用户角色"""
        try:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                return False, "角色不存在"
            user.role = role
            db.session.commit()
            return True, "角色修改成功"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"修改用户角色失败: {str(e)}")
            return False, "角色修改失败，请稍后重试"
    
    def get_user_list(self, page=1, per_page=10):
        """获取用户列表"""
        return User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def search_users(self, keyword, page=1, per_page=10):
        """搜索用户"""
        return User.query.filter(
            (User.username.ilike(f'%{keyword}%')) |
            (User.email.ilike(f'%{keyword}%'))
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
    
    def get_user_stats(self):
        """获取用户统计信息"""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.join(Role).filter(Role.name == 'Administrator').count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users
        } 