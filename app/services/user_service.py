"""
文件名：user_service.py
描述：用户服务类
作者：denny
创建日期：2025-02-16
"""

from app.models import User, db
from sqlalchemy.exc import IntegrityError
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
        return value

    @staticmethod
    def create_user(username, email, password):
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
            user = User(username=username, email=email)
            user.password = password
            db.session.add(user)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("用户创建失败，请检查输入")
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据ID获取用户"""
        try:
            user_id = int(user_id)
            return User.query.get(user_id)
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
    def update_user(user, **kwargs):
        """更新用户信息"""
        try:
            for key, value in kwargs.items():
                if key == 'password':
                    if not value or len(value) < 6:
                        raise ValueError("密码不能为空且长度必须大于6个字符")
                    user.password = value
                elif key in ['username', 'email', 'status']:
                    if key in ['username', 'email']:
                        value = UserService._validate_input(value, key)
                    setattr(user, key, value)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("用户更新失败，请检查输入")
    
    @staticmethod
    def delete_user(user):
        """删除用户"""
        if not user or not isinstance(user, User):
            raise ValueError("无效的用户对象")
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise ValueError("用户删除失败") 