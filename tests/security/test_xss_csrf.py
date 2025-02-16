import pytest
from app.models import User, Post, Comment
from app.services.security import SecurityService
from app.extensions import db

@pytest.fixture
def security_service():
    return SecurityService()

class TestXSSProtection:
    """XSS防护测试 [ST-003]"""

    def test_markdown_xss_protection(self, security_service, test_client):
        """测试Markdown XSS防护"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        # 测试包含XSS攻击的Markdown内容
        xss_markdown_contents = [
            "# Title <script>alert('xss')</script>",
            "[link](<javascript:alert('xss')>)",
            "![image](javascript:alert('xss'))",
            "<img src=x onerror=alert('xss')>",
            "<a href='javascript:alert(\"xss\")'>click me</a>"
        ]

        for content in xss_markdown_contents:
            post = Post(
                title="Test Post",
                content=content,
                author_id=user.id
            )
            db.session.add(post)
            db.session.commit()

            # 验证XSS内容被过滤
            assert '<script>' not in post.html_content
            assert 'javascript:' not in post.html_content
            assert 'onerror=' not in post.html_content

    def test_comment_xss_protection(self, security_service, test_client):
        """测试评论XSS防护"""
        # 创建测试用户和文章
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 测试包含XSS攻击的评论
        xss_comments = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "<a href='javascript:alert(1)'>click</a>",
            "```html\n<script>alert('xss')</script>\n```",
            "<iframe src='javascript:alert(\"xss\")'></iframe>"
        ]

        for content in xss_comments:
            response = test_client.post(f'/post/{post.id}/comment', data={
                'content': content,
                'author_id': user.id
            })
            assert response.status_code == 200

            # 获取最新评论并验证XSS内容被过滤
            comment = Comment.query.order_by(Comment.id.desc()).first()
            assert '<script>' not in comment.html_content
            assert 'javascript:' not in comment.html_content
            assert '<iframe' not in comment.html_content

    def test_input_filtering(self, security_service, test_client):
        """测试输入过滤"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        # 测试各种输入字段
        xss_inputs = {
            'title': '<script>alert("xss")</script>Test Title',
            'content': '<img src=x onerror=alert("xss")>Test Content',
            'email': '"><script>alert("xss")</script>@test.com',
            'username': 'test<script>alert("xss")</script>user'
        }

        # 测试个人资料更新
        response = test_client.post('/profile/update', data=xss_inputs)
        assert response.status_code in [200, 302]

        # 验证存储的数据已被过滤
        user = User.query.filter_by(id=user.id).first()
        assert '<script>' not in user.username
        assert '<script>' not in user.email


class TestCSRFProtection:
    """CSRF防护测试 [ST-004]"""

    def test_form_csrf_protection(self, security_service, test_client):
        """测试表单CSRF保护"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 获取CSRF令牌
        response = test_client.get('/profile')
        csrf_token = security_service.get_csrf_token(response.data)

        # 测试无CSRF令牌的请求
        response = test_client.post('/profile/update', data={
            'email': 'new@example.com'
        })
        assert response.status_code == 403  # 应该被拒绝

        # 测试带有效CSRF令牌的请求
        response = test_client.post('/profile/update', data={
            'email': 'new@example.com',
            'csrf_token': csrf_token
        })
        assert response.status_code == 200  # 应该成功

        # 测试带无效CSRF令牌的请求
        response = test_client.post('/profile/update', data={
            'email': 'new@example.com',
            'csrf_token': 'invalid_token'
        })
        assert response.status_code == 403  # 应该被拒绝

    def test_api_csrf_protection(self, security_service, test_client):
        """测试API CSRF保护"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 测试API端点
        endpoints = [
            ('/api/post/create', 'POST'),
            ('/api/comment/create', 'POST'),
            ('/api/profile/update', 'PUT'),
            ('/api/post/delete/1', 'DELETE')
        ]

        for endpoint, method in endpoints:
            # 测试无CSRF头的请求
            response = test_client.open(endpoint, method=method)
            assert response.status_code == 403

            # 测试带有效CSRF头的请求
            response = test_client.open(
                endpoint,
                method=method,
                headers={'X-CSRF-Token': security_service.generate_csrf_token()}
            )
            assert response.status_code in [200, 201, 404]  # 404是因为资源可能不存在

            # 测试带无效CSRF头的请求
            response = test_client.open(
                endpoint,
                method=method,
                headers={'X-CSRF-Token': 'invalid_token'}
            )
            assert response.status_code == 403

    def test_csrf_token_management(self, security_service, test_client):
        """测试CSRF令牌管理"""
        # 创建测试用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("Test@password123")
        db.session.add(user)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'testuser',
            'password': 'Test@password123'
        })

        # 获取CSRF令牌
        response = test_client.get('/profile')
        csrf_token = security_service.get_csrf_token(response.data)

        # 验证令牌有效性
        assert security_service.validate_csrf_token(csrf_token)

        # 测试令牌过期
        import time
        time.sleep(3600)  # 等待1小时
        assert not security_service.validate_csrf_token(csrf_token)

        # 测试并发请求使用相同令牌
        response = test_client.get('/profile')
        csrf_token = security_service.get_csrf_token(response.data)

        for _ in range(5):
            response = test_client.post('/profile/update', data={
                'email': f'test{_}@example.com',
                'csrf_token': csrf_token
            })
            assert response.status_code == 200  # 同一令牌应该可以多次使用 