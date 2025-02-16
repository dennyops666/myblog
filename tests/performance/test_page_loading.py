import pytest
import time
from app.models import Post, User
from app.extensions import db, cache

class TestPageLoadingPerformance:
    """页面加载性能测试 [PT-001]"""

    def test_homepage_loading(self, test_client):
        """测试首页加载时间"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        for i in range(10):
            post = Post(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                author_id=user.id
            )
            db.session.add(post)
        db.session.commit()

        # 测试加载时间
        start_time = time.time()
        response = test_client.get('/')
        load_time = time.time() - start_time

        assert response.status_code == 200
        assert load_time < 2.0  # 首页加载时间应小于2秒

    def test_article_page_loading(self, test_client):
        """测试文章页面加载时间"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        post = Post(
            title="Test Post",
            content="# Test Content\n" * 100,  # 创建较长的文章内容
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()

        # 测试加载时间
        start_time = time.time()
        response = test_client.get(f'/post/{post.id}')
        load_time = time.time() - start_time

        assert response.status_code == 200
        assert load_time < 3.0  # 文章页面加载时间应小于3秒

    def test_admin_page_loading(self, test_client):
        """测试后台页面加载时间"""
        # 准备测试数据和登录
        admin = User(username="admin", email="admin@example.com", is_admin=True)
        admin.set_password("password123")
        db.session.add(admin)
        db.session.commit()

        test_client.post('/login', data={
            'username': 'admin',
            'password': 'password123'
        })

        # 测试加载时间
        start_time = time.time()
        response = test_client.get('/admin')
        load_time = time.time() - start_time

        assert response.status_code == 200
        assert load_time < 3.0  # 后台页面加载时间应小于3秒


class TestResourceLoadingPerformance:
    """资源加载性能测试 [PT-002]"""

    def test_static_resource_loading(self, test_client):
        """测试静态资源加载时间"""
        resources = [
            '/static/css/style.css',
            '/static/js/main.js',
            '/static/img/logo.png'
        ]

        for resource in resources:
            start_time = time.time()
            response = test_client.get(resource)
            load_time = time.time() - start_time

            assert response.status_code == 200
            assert load_time < 0.5  # 静态资源加载时间应小于0.5秒

    def test_image_optimization(self, test_client):
        """测试图片加载优化效果"""
        # 准备测试图片
        test_images = [
            '/static/img/large.jpg',
            '/static/img/medium.jpg',
            '/static/img/small.jpg'
        ]

        for image in test_images:
            # 测试原始图片加载
            start_time = time.time()
            response = test_client.get(image)
            original_load_time = time.time() - start_time

            # 测试优化后的图片加载
            start_time = time.time()
            response = test_client.get(f'{image}?optimized=1')
            optimized_load_time = time.time() - start_time

            assert response.status_code == 200
            assert optimized_load_time < original_load_time  # 优化后的加载时间应更短

    def test_cache_effectiveness(self, test_client):
        """测试缓存效果"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        post = Post(
            title="Test Post",
            content="Test content",
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()

        # 第一次访问（未缓存）
        start_time = time.time()
        response = test_client.get(f'/post/{post.id}')
        first_load_time = time.time() - start_time

        # 第二次访问（应该使用缓存）
        start_time = time.time()
        response = test_client.get(f'/post/{post.id}')
        cached_load_time = time.time() - start_time

        assert response.status_code == 200
        assert cached_load_time < first_load_time  # 缓存加载应该更快
        assert cached_load_time < 0.1  # 缓存加载时间应小于0.1秒 