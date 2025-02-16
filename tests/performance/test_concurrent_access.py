import pytest
import threading
import time
import queue
from concurrent.futures import ThreadPoolExecutor
from app.models import Post, User, Comment
from app.extensions import db

class TestConcurrentAccessPerformance:
    """并发访问性能测试 [PT-003]"""

    def test_concurrent_page_access(self, test_client):
        """测试并发页面访问"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 模拟50个用户同时访问
        results = queue.Queue()
        def concurrent_request():
            start_time = time.time()
            response = test_client.get(f'/post/{post.id}')
            end_time = time.time()
            results.put({
                'status_code': response.status_code,
                'response_time': end_time - start_time
            })

        threads = []
        for _ in range(50):
            t = threading.Thread(target=concurrent_request)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # 分析结果
        response_times = []
        while not results.empty():
            result = results.get()
            assert result['status_code'] == 200
            response_times.append(result['response_time'])

        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 1.0  # 平均响应时间应小于1秒
        assert max_response_time < 2.0  # 最大响应时间应小于2秒

    def test_concurrent_comment_submission(self, test_client):
        """测试并发评论提交"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 模拟10次/秒的评论提交
        results = queue.Queue()
        def submit_comment(i):
            start_time = time.time()
            response = test_client.post(f'/post/{post.id}/comment', data={
                'content': f'Test comment {i}',
                'author_id': user.id
            })
            end_time = time.time()
            results.put({
                'status_code': response.status_code,
                'response_time': end_time - start_time
            })

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(submit_comment, i) for i in range(10)]
            for future in futures:
                future.result()

        # 验证结果
        success_count = 0
        response_times = []
        while not results.empty():
            result = results.get()
            if result['status_code'] == 200:
                success_count += 1
                response_times.append(result['response_time'])

        assert success_count == 10  # 所有评论都应该成功提交
        assert max(response_times) < 1.0  # 评论提交响应时间应小于1秒

    def test_concurrent_file_upload(self, test_client):
        """测试并发文件上传"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        # 模拟5次/秒的文件上传
        results = queue.Queue()
        def upload_file(i):
            test_file = f'test_file_{i}.txt'
            with open(test_file, 'w') as f:
                f.write(f'Test content {i}')

            start_time = time.time()
            with open(test_file, 'rb') as f:
                response = test_client.post('/upload', data={
                    'file': (f, test_file),
                    'author_id': user.id
                })
            end_time = time.time()
            results.put({
                'status_code': response.status_code,
                'response_time': end_time - start_time
            })

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            for future in futures:
                future.result()

        # 验证结果
        success_count = 0
        response_times = []
        while not results.empty():
            result = results.get()
            if result['status_code'] == 200:
                success_count += 1
                response_times.append(result['response_time'])

        assert success_count == 5  # 所有文件都应该成功上传
        assert max(response_times) < 2.0  # 文件上传响应时间应小于2秒


class TestDatabasePerformance:
    """数据库性能测试 [PT-004]"""

    def test_query_response_time(self, test_client):
        """测试查询响应时间"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        # 创建100篇文章
        for i in range(100):
            post = Post(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                author_id=user.id
            )
            db.session.add(post)
        db.session.commit()

        # 测试不同类型的查询
        queries = [
            lambda: Post.query.all(),
            lambda: Post.query.filter_by(author_id=user.id).all(),
            lambda: Post.query.order_by(Post.created_at.desc()).limit(10).all(),
            lambda: Post.query.filter(Post.title.like('%Test%')).all()
        ]

        for query in queries:
            start_time = time.time()
            result = query()
            query_time = time.time() - start_time

            assert len(result) > 0
            assert query_time < 1.0  # 查询响应时间应小于1秒

    def test_write_performance(self, test_client):
        """测试写入性能"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        # 测试批量写入（100次/秒）
        start_time = time.time()
        posts = []
        for i in range(100):
            post = Post(
                title=f"Test Post {i}",
                content=f"Test content {i}",
                author_id=user.id
            )
            posts.append(post)

        db.session.add_all(posts)
        db.session.commit()
        write_time = time.time() - start_time

        assert write_time < 1.0  # 批量写入时间应小于1秒
        assert Post.query.count() == 100

    def test_cache_performance(self, test_client):
        """测试缓存性能"""
        # 准备测试数据
        user = User(username="testuser", email="test@example.com")
        db.session.add(user)
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 测试100次查询
        cache_hits = 0
        total_queries = 100

        for i in range(total_queries):
            start_time = time.time()
            response = test_client.get(f'/post/{post.id}')
            query_time = time.time() - start_time

            assert response.status_code == 200
            if query_time < 0.01:  # 认为小于10ms的响应是来自缓存
                cache_hits += 1

        cache_hit_rate = cache_hits / total_queries
        assert cache_hit_rate > 0.8  # 缓存命中率应大于80% 