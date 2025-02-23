"""
文件名：user.py
描述：用户服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, UTC
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.services.security import SecurityService
from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.security = SecurityService()
    
    def create_user(self, username, password, email=None, roles=None):
        """创建用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱（可选）
            roles: 角色列表（可选）
            
        Returns:
            User: 创建的用户对象
            
        Raises:
            ValueError: 如果用户名已存在
        """
        if User.query.filter_by(username=username).first():
            raise ValueError('用户名已存在')
            
        user = User(
            username=username,
            email=email,
            is_active=True
        )
        user.password = password
        
        if roles:
            from app.models.role import Role
            for role_name in roles:
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user.add_role(role)
        
        db.session.add(user)
        db.session.commit()
        
        return user
    
    def update_user(self, user_id, username=None, password=None, email=None):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            username: 新用户名（可选）
            password: 新密码（可选）
            email: 新邮箱（可选）
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            if username and username != user.username:
                # 检查新用户名是否已存在
                if User.query.filter_by(username=username).first():
                    return {'status': 'error', 'message': '用户名已存在'}
                user.username = username
                
            if password:
                user.password = generate_password_hash(password)
                
            if email:
                user.email = email
                
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
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            db.session.delete(user)
            db.session.commit()
            
            return {'status': 'success', 'message': '用户删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除用户失败: {str(e)}")
            return {'status': 'error', 'message': '删除用户失败，请稍后重试'}
    
    def get_user(self, user_id):
        """获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            return {'status': 'success', 'user': user}
            
        except Exception as e:
            current_app.logger.error(f"获取用户失败: {str(e)}")
            return {'status': 'error', 'message': '获取用户失败，请稍后重试'}
    
    def get_users(self, page=1, per_page=10):
        """获取用户列表
        
        Args:
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            pagination = User.query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
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
    
    def verify_password(self, user_id, password):
        """验证用户密码
        
        Args:
            user_id: 用户ID
            password: 密码
            
        Returns:
            bool: 密码是否正确
        """
        user = User.query.get(user_id)
        if not user:
            return False
            
        return check_password_hash(user.password, password)
    
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
    
    def search_users(self, keyword, page=1, per_page=10):
        """搜索用户
        
        Args:
            keyword: 关键词
            page: 页码
            per_page: 每页数量
            
        Returns:
            dict: 包含分页信息的字典
        """
        query = User.query.filter(
            User.username.ilike(f'%{keyword}%')
        )
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return {
            'items': pagination.items,
            'page': page,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        }
    
    def get_user_stats(self):
        """获取用户统计信息"""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users
        } 