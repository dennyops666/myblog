"""
文件名：user_service.py
描述：用户服务类
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, List
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.role import Role
from app.models.session import UserSession
from app.extensions import db
import logging
import re

class UserService:
    @staticmethod
    def _sanitize_input(value):
        """清理输入，防止SQL注入"""
        if not isinstance(value, str):
            return value
        # 移除SQL注入相关的特殊字符
        return re.sub(r'[;\'\"\\]', '', value)

    @staticmethod
    def _validate_input(value, field_name, max_length=50):
        """验证输入"""
        if not value or not isinstance(value, str):
            raise ValueError(f"{field_name}不能为空且必须是字符串")
        if len(value) > max_length:
            raise ValueError(f"{field_name}长度不能超过{max_length}个字符")
        if re.search(r'[;\'\"\\]', value):
            raise ValueError(f"{field_name}包含非法字符")
        return value.strip()

    @staticmethod
    def create_user(username, email, password, role_id=None):
        """创建新用户"""
        # 验证和清理输入
        username = UserService._validate_input(username, "用户名")
        email = UserService._validate_input(email, "邮箱")
        if not password or len(password) < 6:
            raise ValueError("密码不能为空且长度必须大于6个字符")
            
        # 验证用户名和邮箱是否已存在
        if UserService.get_user_by_username(username):
            raise ValueError("用户名已存在")
        if UserService.get_user_by_email(email):
            raise ValueError("邮箱已存在")
            
        try:
            user = User(username=username, email=email, role_id=role_id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"创建用户失败：{str(e)}")
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        try:
            user_id = int(user_id)
            return db.session.get(User, user_id)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户"""
        if not username or not isinstance(username, str):
            return None
        username = UserService._sanitize_input(username)
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        """根据邮箱获取用户"""
        if not email or not isinstance(email, str):
            return None
        email = UserService._sanitize_input(email)
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def update_user(user_id: int, username: str = None, email: str = None, 
                   password: str = None, nickname: str = None, 
                   is_active: bool = None, role_ids: List[int] = None) -> Dict[str, Any]:
        """更新用户信息
        
        Args:
            user_id: 用户ID
            username: 用户名
            email: 邮箱
            password: 密码（可选）
            nickname: 昵称（可选）
            is_active: 是否激活
            role_ids: 角色ID列表
            
        Returns:
            dict: 包含更新状态和消息的字典
        """
        try:
            user = db.session.get(User, user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}

            # 验证用户名唯一性
            if username and username != user.username:
                if User.query.filter_by(username=username).first():
                    return {'status': 'error', 'message': '用户名已存在'}
                user.username = username

            # 验证邮箱唯一性
            if email and email != user.email:
                if User.query.filter_by(email=email).first():
                    return {'status': 'error', 'message': '邮箱已存在'}
                user.email = email

            # 更新密码
            if password:
                user.set_password(password)

            # 更新昵称
            if nickname is not None:
                user.nickname = nickname

            # 更新激活状态
            if is_active is not None:
                user.is_active = is_active

            # 更新角色
            if role_ids is not None:
                # 将字符串ID转换为整数
                role_ids = [int(rid) for rid in role_ids]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                user.roles = roles

            db.session.commit()
            return {'status': 'success', 'message': '用户更新成功', 'user': user}
        except Exception as e:
            db.session.rollback()
            return {'status': 'error', 'message': f'更新用户失败：{str(e)}'}
    
    @staticmethod
    def delete_user(user):
        """删除用户"""
        if not user or not isinstance(user, User):
            raise ValueError("无效的用户对象")
        try:
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"删除用户失败：{str(e)}")
    
    @staticmethod
    def get_user_posts(user_id):
        """获取用户的文章列表"""
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return user.posts.all()
    
    @staticmethod
    def get_user_comments(user_id):
        """获取用户的评论列表"""
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        return user.comments.all()
    
    @staticmethod
    def update_profile(user_id, **kwargs):
        """更新用户档案"""
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
            
        allowed_fields = ['nickname', 'bio', 'website', 'avatar_url']
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        return UserService.update_user(user, **update_data)
    
    @staticmethod
    def update_avatar(user_id, avatar_url):
        """更新用户头像"""
        return UserService.update_profile(user_id, avatar_url=avatar_url)
    
    @staticmethod
    def update_social_links(user_id, social_links):
        """更新社交链接"""
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
            
        try:
            user.social_links = social_links
            db.session.commit()
            return user
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"更新社交链接失败：{str(e)}")
    
    @staticmethod
    def delete(user_id):
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Raises:
            ValueError: 当用户不存在或删除失败时
        """
        user = UserService.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
            
        try:
            # 删除用户相关的日志记录
            from app.models.operation_log import OperationLog
            OperationLog.query.filter_by(user_id=user_id).delete()
            
            # 删除用户的所有评论
            from app.models.comment import Comment
            Comment.query.filter_by(author_id=user_id).delete()
            
            # 删除用户的所有帖子
            from app.models.post import Post
            Post.query.filter_by(author_id=user_id).delete()
            
            # 删除用户的所有会话
            UserSession.query.filter_by(user_id=user_id).delete()
            
            # 删除用户
            db.session.delete(user)
            
            # 记录删除操作
            from app.services.log import LogService
            LogService.log_action(1, "delete_user", f"删除用户 ID: {user_id}")  # 使用系统用户ID
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"删除用户失败：{str(e)}")

    def get_user(self, user_id):
        """根据ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 包含用户信息的字典
        """
        try:
            user = db.session.get(User, user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
            return {'status': 'success', 'user': user}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}