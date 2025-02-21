"""
文件名：auth.py
描述：认证服务
作者：denny
创建日期：2024-03-21
"""

from datetime import datetime, timedelta, UTC
from flask import current_app, session, request
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.models.session import Session
from app.models.role import Role
from app.extensions import db
from app.utils.security import generate_token, verify_token
from app.services.security import SecurityService
from app.services.user import UserService
import secrets

class AuthService:
    """认证服务类"""
    
    def __init__(self):
        self.security_service = SecurityService()
        self.user_service = UserService()
        self.max_login_attempts = 5
        self.lockout_duration = 30  # 锁定时间（分钟）
        self._failed_attempts = {}

    def register(self, username, email, password):
        """用户注册
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 清理和验证输入
            username = self.security_service.sanitize_input(username)
            email = self.security_service.sanitize_input(email)
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return {'status': 'error', 'message': '用户名已存在'}
            
            # 检查邮箱是否已存在
            if User.query.filter_by(email=email).first():
                return {'status': 'error', 'message': '邮箱已被注册'}
            
            # 检查密码强度
            if not self.security_service.check_password_strength(password):
                return {'status': 'error', 'message': '密码不符合安全要求'}
            
            # 创建新用户
            user = User(username=username, email=email)
            user.set_password(password)
            
            # 设置默认角色
            default_role = Role.query.filter_by(name='user').first()
            if default_role:
                user.roles.append(default_role)
            
            db.session.add(user)
            db.session.commit()
            
            return {'status': 'success', 'message': '注册成功', 'user': user}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"用户注册失败: {str(e)}")
            return {'status': 'error', 'message': '注册失败，请稍后重试'}

    def login(self, username, password, remember=False):
        """用户登录
        
        Args:
            username: 用户名
            password: 密码
            remember: 是否记住登录状态
            
        Returns:
            dict: 包含登录结果的字典
        """
        try:
            # 清理和验证输入
            username = self.security_service.sanitize_input(username)
            if not username or not password:
                return {'success': False, 'message': '用户名和密码不能为空'}
                
            # 检查账户锁定状态
            if self._is_account_locked(username):
                return {'success': False, 'message': '账户已被锁定，请稍后再试'}
                
            # 获取用户
            user = self.user_service.get_user_by_username(username)
            if not user:
                self._record_failed_attempt(username)
                return {'success': False, 'message': '用户名或密码错误'}
                
            # 验证密码
            if not user.verify_password(password):
                self._record_failed_attempt(username)
                return {'success': False, 'message': '用户名或密码错误'}
                
            # 检查密码强度
            if not self.security_service.check_password_strength(password):
                return {'success': False, 'message': '密码不符合安全要求，请修改密码'}
                
            # 重置失败尝试次数
            self._clear_failed_attempts(username)
            
            # 更新用户状态
            user.last_login = datetime.now(UTC)
            user.last_seen = datetime.now(UTC)
            
            # 初始化会话
            session.clear()  # 清除现有会话
            session['user_id'] = user.id
            session['_fresh'] = True
            session['_permanent'] = True
            session.permanent = True
            
            # 生成新的CSRF令牌
            csrf_token = secrets.token_urlsafe(32)
            session['csrf_token'] = csrf_token
            
            # 记录会话信息
            session['last_active'] = datetime.now(UTC).isoformat()
            session['user_agent'] = request.user_agent.string if request else None
            session.modified = True
            
            # 登录用户
            login_user(user, remember=remember, fresh=True)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': '登录成功',
                'user': user,
                'csrf_token': csrf_token
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"登录失败: {str(e)}")
            return {'success': False, 'message': '登录过程中发生错误'}

    def logout(self):
        """用户登出
        
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            if not session.get('user_id'):
                return {'success': True, 'message': '已登出'}
                
            # 获取当前会话
            user_session = Session.query.filter_by(
                user_id=session['user_id'],
                is_active=True
            ).first()
            
            if user_session:
                # 使会话失效
                user_session.invalidate()
                db.session.commit()
            
            # 登出用户
            logout_user()
            
            # 清除会话
            session.clear()
            
            return {'success': True, 'message': '已安全登出'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"用户登出失败: {str(e)}")
            return {'success': False, 'message': '登出失败，请稍后重试'}

    def change_password(self, user, old_password, new_password):
        """修改密码
        
        Args:
            user: 用户对象
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 验证旧密码
            if not user.verify_password(old_password):
                return {'status': 'error', 'message': '原密码错误'}
            
            # 检查新密码强度
            if not self.security_service.check_password_strength(new_password):
                return {'status': 'error', 'message': '新密码不符合安全要求'}
            
            # 更新密码
            user.set_password(new_password)
            db.session.commit()
            
            # 清除所有会话
            Session.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            
            return {'status': 'success', 'message': '密码修改成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"修改密码失败: {str(e)}")
            return {'status': 'error', 'message': '密码修改失败，请稍后重试'}

    def reset_password(self, email):
        """重置密码
        
        Args:
            email: 用户邮箱
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 清理输入
            email = self.security_service.sanitize_input(email)
            
            # 获取用户
            user = User.query.filter_by(email=email).first()
            if not user:
                return {'status': 'error', 'message': '邮箱不存在'}
            
            # TODO: 实现密码重置邮件发送逻辑
            
            return {'status': 'success', 'message': '密码重置邮件已发送'}
            
        except Exception as e:
            current_app.logger.error(f"重置密码失败: {str(e)}")
            return {'status': 'error', 'message': '重置密码失败，请稍后重试'}

    def confirm_reset_password(self, token, new_password):
        """确认重置密码
        
        Args:
            token: 重置令牌
            new_password: 新密码
            
        Returns:
            dict: 包含状态和消息的字典
        """
        try:
            # 验证令牌
            user_id = verify_token(token)
            if not user_id:
                return {'status': 'error', 'message': '无效或过期的重置令牌'}
            
            # 获取用户
            user = User.query.get(user_id)
            if not user:
                return {'status': 'error', 'message': '用户不存在'}
            
            # 检查新密码强度
            if not self.security_service.check_password_strength(new_password):
                return {'status': 'error', 'message': '新密码不符合安全要求'}
            
            # 更新密码
            user.set_password(new_password)
            db.session.commit()
            
            # 清除所有会话
            Session.query.filter_by(user_id=user.id).delete()
            db.session.commit()
            
            return {'status': 'success', 'message': '密码重置成功'}
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"确认重置密码失败: {str(e)}")
            return {'status': 'error', 'message': '密码重置失败，请稍后重试'}

    def _is_account_locked(self, username):
        """检查账户是否被锁定"""
        attempts = self._get_failed_attempts(username)
        return attempts.get('count', 0) >= self.max_login_attempts and \
            attempts.get('timestamp', datetime.min) + timedelta(minutes=self.lockout_duration) > datetime.now(UTC)

    def _record_failed_attempt(self, username):
        """记录失败的登录尝试"""
        attempts = self._get_failed_attempts(username)
        attempts['count'] = attempts.get('count', 0) + 1
        attempts['timestamp'] = datetime.now(UTC)
        self._failed_attempts[username] = attempts

    def _get_failed_attempts(self, username):
        """获取失败的登录尝试记录"""
        return self._failed_attempts.get(username, {'count': 0, 'timestamp': datetime.min})

    def _clear_failed_attempts(self, username):
        """清除失败的登录尝试记录"""
        if username in self._failed_attempts:
            del self._failed_attempts[username]