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
from app.models.role import Role
from app.services.security import SecurityService
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.security = SecurityService()
    
    def create_user(self, username, password, email, nickname=None, role_ids=None, is_active=True):
        """创建用户
        
        Args:
            username: 用户名
            password: 密码
            email: 邮箱
            nickname: 昵称（可选）
            role_ids: 角色ID列表（可选）
            is_active: 是否启用账号
            
        Returns:
            dict: 包含状态和消息的字典
            
        Raises:
            ValueError: 如果用户名已存在或其他错误
        """
        try:
            # 验证用户名
            if not username or len(username) < 3:
                return {'status': 'error', 'message': '用户名长度不能小于3个字符'}
                
            # 检查是否尝试创建超级管理员
            super_admin = User.query.get(1)
            if super_admin and username == super_admin.username:
                return {'status': 'error', 'message': '不能创建与超级管理员相同用户名的用户'}
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return {'status': 'error', 'message': '用户名已存在'}
            
            # 验证邮箱
            if not email:
                return {'status': 'error', 'message': '邮箱不能为空'}
                
            if User.query.filter_by(email=email).first():
                return {'status': 'error', 'message': '邮箱已被使用'}
            
            # 验证密码
            if not password or len(password) < 6:
                return {'status': 'error', 'message': '密码长度不能小于6个字符'}
            
            # 创建用户对象
            user = User(
                username=username,
                email=email,
                nickname=nickname or username,
                is_active=is_active
            )
            user.set_password(password)
            
            # 分配角色
            if role_ids:
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                user.roles = roles
            else:
                # 如果没有指定角色，添加默认角色
                default_role = Role.query.filter_by(name='user').first()
                if default_role:
                    user.roles.append(default_role)
            
            # 保存到数据库
            db.session.add(user)
            db.session.commit()
            
            return {'status': 'success', 'message': '用户创建成功', 'user': user}
            
        except IntegrityError as e:
            db.session.rollback()
            if 'users.username' in str(e):
                return {'status': 'error', 'message': '用户名已存在'}
            elif 'users.email' in str(e):
                return {'status': 'error', 'message': '邮箱已存在'}
            return {'status': 'error', 'message': '创建用户失败'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建用户失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def update_user(self, user_id, username=None, email=None, password=None, 
                   nickname=None, is_active=None, role_ids=None):
        """更新用户信息
        
        Args:
            user_id: 用户ID
            username: 新用户名（可选）
            email: 新邮箱（可选）
            password: 新密码（可选）
            nickname: 新昵称（可选）
            is_active: 是否启用账号（可选）
            role_ids: 新角色ID列表（可选）
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
                
            if username is not None:
                user.username = username
            if email is not None:
                user.email = email
            if password:
                user.set_password(password)
            if nickname is not None:
                user.nickname = nickname
            if is_active is not None:
                user.is_active = is_active
                
            # 更新角色
            if role_ids is not None:
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                user.roles = roles
                
            user.updated_at = datetime.now(UTC)
            db.session.commit()
            
            return {'status': 'success', 'message': '用户更新成功', 'user': user}
            
        except IntegrityError as e:
            db.session.rollback()
            if 'users.username' in str(e):
                return {'status': 'error', 'message': '用户名已存在'}
            elif 'users.email' in str(e):
                return {'status': 'error', 'message': '邮箱已存在'}
            return {'status': 'error', 'message': '更新用户失败'}
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"更新用户失败: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def delete_user(self, user_id):
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = db.session.get(User, user_id)
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
                'pagination': pagination
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
        user = db.session.get(User, user_id)
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