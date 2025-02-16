"""
文件名：user_service.py
描述：用户服务类
作者：denny
创建日期：2025-02-16
"""

from app.models import User, db
from sqlalchemy.exc import IntegrityError

class UserService:
    @staticmethod
    def create_user(username, email, password):
        """创建新用户"""
        # 验证输入
        if not username or not email or not password:
            raise ValueError("用户名、邮箱和密码不能为空")
            
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
        return User.query.get(user_id)
    
    @staticmethod
    def get_user_by_username(username):
        """根据用户名获取用户"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        """根据邮箱获取用户"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def update_user(user, **kwargs):
        """更新用户信息"""
        try:
            for key, value in kwargs.items():
                if key == 'password':
                    user.password = value
                elif hasattr(user, key):
                    setattr(user, key, value)
            db.session.commit()
            return user
        except IntegrityError:
            db.session.rollback()
            raise ValueError("用户更新失败，请检查输入")
    
    @staticmethod
    def delete_user(user):
        """删除用户"""
        try:
            db.session.delete(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise ValueError("用户删除失败") 