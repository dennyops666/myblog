"""
文件名：conftest.py
描述：测试配置
作者：denny
创建日期：2025-02-16
"""

import os
import tempfile
from datetime import timedelta
import pytest
from app import create_app, db
from app.models import User, Post, Category, Tag, Comment

@pytest.fixture
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 创建测试配置
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = True  # 启用CSRF保护
        SECRET_KEY = 'test-key'
        PERMANENT_SESSION_LIFETIME = timedelta(days=7)
        SESSION_COOKIE_SECURE = True
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 创建应用实例
    app = create_app('testing')
    app.config.from_object(TestConfig)
    
    # 确保在测试环境中使用测试数据库
    with app.app_context():
        db.drop_all()  # 确保清理旧数据
        db.create_all()  # 创建新表
        db.session.commit()  # 提交更改
    
    yield app
    
    # 清理
    with app.app_context():
        db.session.remove()  # 移除所有会话
        db.drop_all()  # 删除所有表
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建测试命令行运行器"""
    return app.test_cli_runner()

@pytest.fixture
def app_context(app):
    """创建应用上下文"""
    with app.app_context() as ctx:
        yield ctx
        db.session.rollback()  # 回滚未提交的更改

@pytest.fixture
def test_user(app_context):
    """创建测试用户"""
    user = User(
        username='test',
        email='test@example.com'
    )
    user.set_password('password')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_category(app_context):
    """创建测试分类"""
    category = Category(name='测试分类')
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_tag(app_context):
    """创建测试标签"""
    tag = Tag(name='测试标签')
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture
def test_post(app_context, test_user, test_category):
    """创建测试文章"""
    post = Post(
        title='测试文章',
        content='这是一篇测试文章的内容',
        category_id=test_category.id,
        author_id=test_user.id,
        status=1
    )
    db.session.add(post)
    db.session.commit()
    return post

@pytest.fixture
def test_comment(app_context, test_post, test_user):
    """创建测试评论"""
    comment = Comment(
        content='这是一条测试评论',
        post_id=test_post.id,
        author_id=test_user.id,
        status=1
    )
    db.session.add(comment)
    db.session.commit()
    return comment

@pytest.fixture
def auth(client):
    """认证辅助类"""
    class AuthActions:
        def __init__(self, client):
            self._client = client
            
        def login(self, username='test', password='password'):
            with client.session_transaction() as session:
                session.permanent = True  # 设置会话为永久
            return self._client.post(
                '/auth/login',
                data={'username': username, 'password': password},
                follow_redirects=True
            )
            
        def logout(self):
            return self._client.get('/auth/logout', follow_redirects=True)
    
    return AuthActions(client) 