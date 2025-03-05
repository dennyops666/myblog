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
import re

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
        """
        try:
            # 验证用户名
            if not username or len(username) < 3:
                return {'status': False, 'message': '用户名长度不能小于3个字符'}
                
            # 检查是否尝试创建超级管理员
            if username == 'admin':
                return {'status': False, 'message': '不能创建超级管理员用户'}
            
            # 验证邮箱
            if not email:
                return {'status': False, 'message': '邮箱不能为空'}
            
            # 验证密码
            result = self.validate_password(password)
            if not result['success']:
                return {'status': False, 'message': result['message']}
            
            # 检查用户名和邮箱是否已存在
            if User.query.filter_by(username=username).first():
                return {'status': False, 'message': '该用户名已被使用'}
                
            if User.query.filter_by(email=email).first():
                return {'status': False, 'message': '该邮箱已被使用'}
            
            # 创建用户对象
            user = User(
                username=username,
                email=email,
                nickname=nickname or username,
                is_active=True if is_active in [True, 'on', 1, '1'] else False  # 处理各种可能的is_active值
            )
            user.set_password(password)
            
            # 分配角色
            if role_ids:
                # 过滤掉 super_admin 角色
                roles = Role.query.filter(
                    Role.id.in_(role_ids),
                    Role.name != 'super_admin'
                ).all()
                user.roles = roles
            else:
                # 如果没有指定角色，添加默认角色
                default_role = Role.query.filter_by(name='user').first()
                if default_role:
                    user.roles.append(default_role)
            
            # 保存到数据库
            db.session.add(user)
            db.session.commit()
            
            return {'status': True, 'message': '用户创建成功', 'user': user}
                
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"创建用户失败: {str(e)}")
            return {'status': False, 'message': '创建用户失败'}
    
    @staticmethod
    def validate_password(password):
        """
        验证密码是否符合要求
        :param password: 密码
        :return: 验证结果和错误消息
        """
        if not password:
            return {'success': False, 'message': '密码不能为空'}
        
        if len(password) < 6:
            return {'success': False, 'message': '长度至少6位，必须包含字母和数字'}
        
        if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
            return {'success': False, 'message': '长度至少6位，必须包含字母和数字'}
        
        return {'success': True, 'message': '密码验证通过'}

    def update_user(self, user_id, username=None, email=None, nickname=None, password=None, is_active=None, role_ids=None):
        """更新用户信息"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': False, 'message': '用户不存在'}
                
            # 特殊处理超级管理员用户
            if user.username == 'admin':
                # 不允许修改用户名
                if username and username != 'admin':
                    return {'status': False, 'message': '不能修改超级管理员的用户名'}
                    
                # 强制设置超级管理员角色，忽略传入的role_ids
                super_admin_role = Role.query.filter_by(name='super_admin').first()
                if not super_admin_role:
                    return {'status': False, 'message': '系统错误：未找到超级管理员角色'}
                
                # 确保只有super_admin角色
                if user.roles != [super_admin_role]:
                    user.roles = [super_admin_role]
                
                # 忽略is_active参数，始终保持激活状态
                if is_active is not None and not is_active:
                    return {'status': False, 'message': '不能修改超级管理员的状态'}
                user.is_active = True
            else:
                # 对于普通用户，验证用户名唯一性
                if username and username != user.username:
                    # 不允许使用 admin 作为用户名
                    if username == 'admin':
                        return {'status': False, 'message': '不能使用 admin 作为用户名'}
                    if User.query.filter_by(username=username).first():
                        return {'status': False, 'message': '用户名已存在'}
                    user.username = username
                
                # 设置激活状态
                if is_active is not None:
                    user.is_active = bool(is_active)
                
                # 更新角色（非超级管理员）
                if role_ids is not None:
                    # 将字符串ID转换为整数
                    role_ids = [int(rid) for rid in role_ids if rid]
                    # 获取选中的角色，排除超级管理员角色
                    selected_roles = Role.query.filter(
                        Role.id.in_(role_ids),
                        Role.name != 'super_admin'
                    ).all()
                    # 更新用户的角色
                    user.roles = selected_roles
                
            # 验证邮箱唯一性
            if email and email != user.email:
                if User.query.filter_by(email=email).first():
                    return {'status': False, 'message': '邮箱已存在'}
                user.email = email
                
            # 更新昵称
            if nickname is not None:
                user.nickname = nickname
                
            # 更新密码
            if password:
                # 验证密码格式
                result = self.validate_password(password)
                if not result['success']:
                    return {'status': False, 'message': result['message']}
                user.set_password(password)
            
            # 更新时间
            user.updated_at = datetime.now(UTC)
            
            # 保存更改
            db.session.commit()
            
            return {'status': True, 'message': '更新成功', 'user': user}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新用户失败: {str(e)}')
            return {'status': False, 'message': '更新失败'}
    
    def can_delete_user(self, current_user, target_user):
        """检查当前用户是否可以删除目标用户
        
        Args:
            current_user: 当前登录用户
            target_user: 要删除的目标用户
            
        Returns:
            bool: 是否可以删除
        """
        # 不能删除超级管理员
        if target_user.username == 'admin':
            return False
            
        # 不能删除自己
        if current_user.id == target_user.id:
            return False
            
        # 超级管理员可以删除任何用户（除了自己和其他超级管理员）
        if current_user.username == 'admin':
            return True
            
        # 检查当前用户是否是管理员
        is_admin = any(role.name == 'admin' for role in current_user.roles)
        if not is_admin:
            return False
            
        # 管理员只能删除普通用户
        target_is_admin = any(role.name == 'admin' for role in target_user.roles)
        return not target_is_admin
    
    def delete_user(self, current_user, user_id):
        """删除用户
        
        Args:
            current_user: 当前登录用户
            user_id: 要删除的用户ID
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'status': False, 'message': '用户不存在'}
                
            # 检查是否有权限删除
            if not self.can_delete_user(current_user, user):
                return {'status': False, 'message': '没有权限删除该用户'}
                
            # 先删除该用户的操作日志
            from app.models.operation_log import OperationLog
            OperationLog.query.filter_by(user_id=user_id).delete()
            
            # 删除用户
            db.session.delete(user)
            db.session.commit()
            
            return {'status': True, 'message': '用户删除成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"删除用户失败: {str(e)}")
            current_app.logger.exception(e)  # 记录完整的异常堆栈
            return {'status': False, 'message': '删除用户失败，请稍后重试'}
    
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
    
    def get_users(self, page=1, per_page=10, current_user=None):
        """获取用户列表
        
        Args:
            page: 页码
            per_page: 每页数量
            current_user: 当前登录用户
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            query = User.query
            
            # 如果不是超级管理员，则过滤掉超级管理员用户
            if current_user and current_user.username != 'admin':
                query = query.filter(User.username != 'admin')
            
            # 执行分页查询
            pagination = query.paginate(
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
            return {'status': 'error', 'message': '获取用户列表失败'}
    
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
            dict: 包含用户信息和状态的字典
        """
        if not username:
            return {'success': False, 'message': '用户名不能为空'}
            
        try:
            user = User.query.filter_by(username=username).first()
            if not user:
                return {'success': False, 'message': '用户不存在'}
                
            # 检查用户状态
            if not user.is_active:
                current_app.logger.warning(f'禁用账号尝试登录: {username}')
                return {'success': False, 'message': '您的账号已被禁用，请联系管理员'}
                
            return {'success': True, 'message': '获取用户成功', 'user': user}
            
        except Exception as e:
            current_app.logger.error(f"获取用户失败: {str(e)}")
            return {'success': False, 'message': '获取用户失败'}
    
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