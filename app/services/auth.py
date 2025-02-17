"""
文件名：auth.py
描述：认证服务
作者：denny
创建日期：2025-02-16
"""

from datetime import datetime, timedelta, UTC
from flask_login import login_user, logout_user, current_user
from app.models import User, db
from app.extensions import cache
import secrets
from typing import Optional, Dict, Any, List
from app.models.session import Session

class AuthService:
    """认证服务类"""
    
    TOKEN_EXPIRY = 30 * 24 * 60 * 60  # 30天
    
    def __init__(self):
        self.login_attempts = {}
        self.session_store = {}
    
    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Dict[str, Any]: 登录结果，包含以下字段：
                - success: 是否成功
                - message: 提示信息
                - user: 用户对象（如果成功）
                - token: 会话令牌（如果成功）
        """
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return {
                'success': False,
                'message': '用户名或密码错误'
            }
        
        # 生成会话令牌
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(seconds=AuthService.TOKEN_EXPIRY)
        
        # 创建会话记录
        session = Session(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(session)
        
        # 更新用户最后登录时间
        user.last_login = datetime.now(UTC)
        db.session.commit()
        
        # 缓存会话信息
        cache_key = f'session_{token}'
        session_data = {
            'user_id': user.id,
            'expires_at': expires_at
        }
        cache.set(cache_key, session_data, timeout=AuthService.TOKEN_EXPIRY)
        
        return {
            'success': True,
            'message': '登录成功',
            'user': user,
            'token': token
        }
    
    def create_session(self, user_id, device=None):
        """创建会话
        
        参数：
            user_id: 用户ID
            device: 设备标识
            
        返回：
            dict: 会话信息
        """
        user = User.query.get(user_id)
        if not user:
            return None
            
        session = {
            'id': str(user_id),
            'token': self._generate_session_token(),
            'device': device,
            'created_at': datetime.now(UTC),
            'expires_at': datetime.now(UTC) + timedelta(days=7)
        }
        
        # 存储会话信息
        cache_key = f'session_{session["token"]}'
        cache.set(cache_key, session, timeout=7*24*60*60)  # 7天过期
        
        return session
    
    @staticmethod
    def validate_session(token: str) -> bool:
        """验证会话
        
        Args:
            token: 会话令牌
            
        Returns:
            bool: 会话是否有效
        """
        if not token:
            return False
        
        cache_key = f'session_{token}'
        session = cache.get(cache_key)
        
        if not session:
            # 从数据库中查找
            db_session = Session.query.filter_by(token=token).first()
            if not db_session:
                return False
                
            # 更新缓存
            session = {
                'user_id': db_session.user_id,
                'expires_at': db_session.expires_at
            }
            cache.set(cache_key, session, timeout=AuthService.TOKEN_EXPIRY)
        
        # 检查会话是否过期
        if datetime.now(UTC) > session['expires_at']:
            cache.delete(cache_key)
            return False
            
        return True
    
    @staticmethod
    def get_active_sessions(user_id: int) -> List[Session]:
        """获取用户的活动会话列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Session]: 活动会话列表
        """
        now = datetime.now(UTC)
        return Session.query.filter(
            Session.user_id == user_id,
            Session.expires_at > now
        ).all()
    
    @staticmethod
    def logout(token: str) -> bool:
        """注销会话
        
        Args:
            token: 会话令牌
            
        Returns:
            bool: 是否成功注销
        """
        if not token:
            return False
            
        # 删除缓存
        cache_key = f'session_{token}'
        cache.delete(cache_key)
        
        # 删除数据库记录
        session = Session.query.filter_by(token=token).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
            
        return False
    
    def check_login_attempts(self, user):
        """检查登录尝试次数"""
        if not user:
            return True
            
        attempts = self.login_attempts.get(user.id, {})
        if not attempts:
            return True
            
        # 如果锁定时间未过期且尝试次数超过限制
        if (attempts.get('locked_until') and 
            datetime.now(UTC) < attempts['locked_until'] and 
            attempts.get('count', 0) >= 5):
            return False
            
        return True
    
    def handle_failed_login(self, user):
        """处理登录失败"""
        if not user:
            return
            
        attempts = self.login_attempts.get(user.id, {'count': 0})
        attempts['count'] = attempts.get('count', 0) + 1
        
        # 如果失败次数超过限制，锁定账户30分钟
        if attempts['count'] >= 5:
            attempts['locked_until'] = datetime.now(UTC) + timedelta(minutes=30)
            
        self.login_attempts[user.id] = attempts
    
    def reset_login_attempts(self, user):
        """重置登录尝试次数"""
        if not user:
            return
            
        if user.id in self.login_attempts:
            del self.login_attempts[user.id]
    
    def _generate_session_token(self):
        """生成会话令牌"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """
        验证会话token
        
        Args:
            token: 会话token
            
        Returns:
            Optional[Dict]: 会话信息
        """
        # 先从缓存中获取
        cache_key = f"session:{token}"
        session_data = cache.get(cache_key)
        
        if session_data:
            # 检查是否过期
            if session_data["expires_at"] < datetime.utcnow().timestamp():
                cache.delete(cache_key)
                return None
            return session_data
            
        # 缓存中没有,从数据库查询
        session = Session.query.filter_by(token=token).first()
        if not session or session.expires_at < datetime.utcnow():
            return None
            
        # 更新缓存
        cache_data = {
            "user_id": session.user_id,
            "username": session.user.username,
            "expires_at": session.expires_at.timestamp()
        }
        cache.set(cache_key, cache_data, timeout=AuthService.TOKEN_EXPIRY)
        
        return cache_data
    
    @staticmethod
    def has_permission(user_id, permission):
        """检查用户是否有指定权限
        
        Args:
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        user = db.session.get(User, user_id)
        if not user or not user.role:
            return False
        return permission in user.role.permissions

    @staticmethod
    def _generate_token() -> str:
        """生成随机token"""
        return secrets.token_urlsafe(32) 