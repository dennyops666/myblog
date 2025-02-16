"""
文件名：conftest.py
描述：测试配置文件
作者：denny
创建日期：2025-02-16
"""

import os
import tempfile
import pytest
from app import create_app
from app.models import db, User, Category, Tag, Post, Comment
from flask import g

@pytest.fixture
def app():
    """创建测试应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 创建测试配置
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False
    }
    
    # 创建应用实例
    app = create_app('testing')
    app.config.update(test_config)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 创建测试用户
        user = User(username='admin', email='admin@example.com')
        user.password = 'password'
        db.session.add(user)
        db.session.commit()
    
    yield app
    
    # 清理
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def app_context(app):
    """创建应用上下文"""
    with app.app_context() as ctx:
        yield ctx

@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建测试命令运行器"""
    return app.test_cli_runner()

@pytest.fixture
def auth(client):
    """认证辅助类"""
    class AuthActions:
        def __init__(self, client):
            self._client = client
            
        def login(self, username='admin', password='password'):
            return self._client.post(
                '/admin/login',
                data={'username': username, 'password': password}
            )
            
        def logout(self):
            return self._client.get('/admin/logout')
    
    return AuthActions(client)

@pytest.fixture
def test_user(app_context):
    """创建测试用户"""
    user = User(username='test', email='test@example.com')
    user.password = 'password'
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_category(app_context):
    """创建测试分类"""
    category = Category(name='测试分类', description='这是一个测试分类')
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
def test_comment(app_context, test_post):
    """创建测试评论"""
    comment = Comment(
        content='这是一条测试评论',
        post_id=test_post.id,
        author_name='测试用户',
        author_email='test@example.com',
        status=1
    )
    db.session.add(comment)
    db.session.commit()
    return comment 