import pytest
import re
from app.models import User
from app.services.auth import AuthService
from app.extensions import db

@pytest.fixture
def auth_service():
    return AuthService()

class TestPasswordSecurity:
    """密码安全测试 [ST-001]"""

    def test_password_encryption(self, auth_service):
        """测试密码加密存储"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        password = "Test@password123"
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # 验证密码已加密存储
        assert user.password_hash != password
        assert len(user.password_hash) > 20
        assert user.check_password(password)

    def test_password_complexity(self, auth_service):
        """测试密码复杂度要求"""
        weak_passwords = [
            "password",  # 太简单
            "12345678",  # 只有数字
            "abcdefgh",  # 只有小写字母
            "ABCDEFGH",  # 只有大写字母
            "pass@word",  # 太短
        ]

        strong_passwords = [
            "Test@password123",  # 包含大小写字母、数字和特殊字符
            "Complex@Pass789",   # 符合所有要求
            "Security#2023Pass", # 足够复杂
        ]

        for password in weak_passwords:
            assert not auth_service.check_password_strength(password)

        for password in strong_passwords:
            assert auth_service.check_password_strength(password)

    def test_password_retry_limit(self, auth_service, test_client):
        """测试密码重试限制"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        # 尝试多次错误登录
        for _ in range(5):
            response = test_client.post('/login', data={
                'username': 'testuser',
                'password': 'wrong_password'
            })
            assert response.status_code == 401

        # 验证账户是否被锁定
        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'  # 正确密码
        })
        assert response.status_code == 403  # 账户已锁定

        # 等待锁定时间过后
        import time
        time.sleep(300)  # 等待5分钟

        # 验证可以重新登录
        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })
        assert response.status_code == 200


class TestSessionSecurity:
    """会话安全测试 [ST-002]"""

    def test_session_management(self, auth_service, test_client):
        """测试会话管理"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })
        assert response.status_code == 200

        # 验证会话属性
        session_cookie = next(
            (cookie for cookie in test_client.cookie_jar if cookie.name == 'session'),
            None
        )
        assert session_cookie is not None
        assert session_cookie.secure  # 确保使用HTTPS
        assert session_cookie.httponly  # 防止XSS访问
        assert session_cookie.samesite == 'Lax'  # CSRF保护

    def test_cookie_security(self, auth_service, test_client):
        """测试Cookie安全"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 验证Cookie设置
        cookies = response.headers.getlist('Set-Cookie')
        for cookie in cookies:
            assert 'Secure' in cookie
            assert 'HttpOnly' in cookie
            assert 'SameSite' in cookie
            assert not re.search(r'Max-Age=\d+', cookie)  # 会话Cookie

    def test_login_protection(self, auth_service, test_client):
        """测试登录保护"""
        # 测试CSRF保护
        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert response.status_code == 400  # 缺少CSRF令牌

        # 测试同源策略
        response = test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        }, headers={'Origin': 'http://malicious-site.com'})
        assert response.status_code == 403  # 不允许跨域请求

        # 测试请求频率限制
        for _ in range(10):
            response = test_client.post('/login', data={
                'username': 'testuser',
                'password': 'Test@password123'
            })
        assert response.status_code == 429  # 请求过于频繁 