"""
文件名：auth.py
描述：认证服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, timedelta, UTC
from flask_login import login_user, logout_user, current_user
from app.models import User, db
from app.extensions import cache
import secrets
from typing import Optional, Dict, Any, List
from app.models.session import Session
import jwt

class AuthService:
    """认证服务类"""
    
    TOKEN_EXPIRY = 30 * 24 * 60 * 60  # 30天
    
    def __init__(self):
        self.login_attempts = {}
        self.session_store = {}
        self.secret_key = "your-secret-key"  # 在生产环境中应该使用环境变量
    
    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Dict: 包含token和user信息的字典
            
        Raises:
            ValueError: 当登录失败时抛出
        """
        if not username or not password:
            raise ValueError("用户名和密码不能为空")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            raise ValueError("用户名或密码错误")

        # 创建新会话
        session = Session(
            user_id=user.id,
            token=AuthService._generate_token(),
            expires_at=datetime.now(UTC) + timedelta(days=30)
        )

        # 更新用户最后登录时间
        user.last_login = datetime.now(UTC)

        try:
            db.session.add(session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"创建会话失败：{str(e)}")

        return {
            'success': True,
            'token': session.token,
            'user': user
        }
    
    def create_session(self, user_id, device=None):
        """创建新会话
        
        Args:
            user_id: 用户ID
            device: 设备信息（可选）
            
        Returns:
            Session: 会话对象
        """
        # 生成会话令牌
        token = self._generate_session_token()
        
        # 创建新会话
        session = Session(
            user_id=user_id,
            token=token,
            expires_at=datetime.now(UTC) + timedelta(days=30)  # 使用带时区的时间
        )
        
        try:
            db.session.add(session)
            db.session.commit()
            return session
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"创建会话失败：{str(e)}")
    
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
            
        session = Session.query.filter_by(token=token).first()
        if not session:
            return False
            
        # 确保使用带时区的时间进行比较
        current_time = datetime.now(UTC)
        if session.expires_at.replace(tzinfo=UTC) < current_time:
            # 会话过期，删除会话
            db.session.delete(session)
            db.session.commit()
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
        return Session.query.filter(
            Session.user_id == user_id,
            Session.expires_at > datetime.now(UTC)
        ).all()
    
    @staticmethod
    def logout(token: str) -> bool:
        """用户登出
        
        Args:
            token: 会话令牌
            
        Returns:
            bool: 是否成功登出
        """
        if not token:
            return False
            
        session = Session.query.filter_by(token=token).first()
        if session:
            try:
                db.session.delete(session)
                db.session.commit()
                return True
            except Exception:
                db.session.rollback()
                return False
        return False
    
    def check_login_attempts(self, user):
        """检查登录尝试次数"""
        key = f'login_attempts_{user.id}'
        attempts = cache.get(key) or 0
        return attempts
    
    def handle_failed_login(self, user):
        """处理登录失败"""
        key = f'login_attempts_{user.id}'
        attempts = cache.get(key) or 0
        attempts += 1
        
        # 设置缓存，5分钟后过期
        cache.set(key, attempts, timeout=300)
        
        if attempts >= 5:
            # 锁定账户
            user.is_active = False
            db.session.commit()
    
    def reset_login_attempts(self, user):
        """重置登录尝试次数"""
        key = f'login_attempts_{user.id}'
        cache.delete(key)
    
    def _generate_session_token(self):
        """生成会话令牌"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def validate_token(token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌
        
        Args:
            token: JWT令牌
            
        Returns:
            Optional[Dict]: 令牌中的数据
        """
        try:
            # 解码令牌
            session_data = jwt.decode(
                token,
                "your-secret-key",  # 在生产环境中应该使用环境变量
                algorithms=["HS256"]
            )
            
            # 检查是否过期
            if session_data["expires_at"] < datetime.now(UTC).timestamp():
                return None
                
            # 验证会话是否存在
            session = Session.query.filter_by(token=token).first()
            if not session or session.expires_at < datetime.now(UTC):
                return None
                
            return session_data
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def has_permission(user_id, permission):
        """检查用户是否有指定权限
        
        Args:
            user_id: 用户ID
            permission: 权限名称
            
        Returns:
            bool: 是否有权限
        """
        user = User.query.get(user_id)
        if not user or not user.role:
            return False
            
        return permission in user.role.permissions
    
    @staticmethod
    def _generate_token() -> str:
        """生成随机令牌"""
        return secrets.token_urlsafe(32) 