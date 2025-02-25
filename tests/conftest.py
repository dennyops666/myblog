"""
文件名：conftest.py
描述：测试配置和夹具
作者：denny
创建日期：2024-03-21
"""

import os
import tempfile
import pytest
from datetime import datetime, UTC
from contextlib import contextmanager
from flask_wtf.csrf import generate_csrf
from app import create_app
from app.extensions import db
from app.models import User, Category, Post, Tag, Comment, Role
from app.models.post import PostStatus
import shutil
import markdown2
from sqlalchemy import event
from bs4 import BeautifulSoup
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import login_user
from flask import session
import secrets
from werkzeug.datastructures import MultiDict, FileStorage

@contextmanager
def session_scope():
    """提供事务作用域的上下文管理器"""
    try:
        yield db.session
        db.session.commit()
    except:
        db.session.rollback()
        raise
    finally:
        db.session.close()

@pytest.fixture(autouse=True)
def db_session(app):
    """创建数据库会话"""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        
        session_factory = sessionmaker(bind=connection)
        session = scoped_session(session_factory)
        
        # 替换 Flask-SQLAlchemy 的会话
        db.session = session
        
        yield session
        
        session.remove()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope='session')
def app():
    """创建应用实例"""
    app = create_app('testing')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
    yield app
    
    # 清理数据库
    with app.app_context():
        db.drop_all()

@pytest.fixture(scope='function')
def test_user(app, db_session):
    """创建测试用户"""
    user = User.query.filter_by(username='test').first()
    if not user:
        user = User(
            username='test',
            email='test@example.com'
        )
        user.set_password('test')
        db.session.add(user)
        db.session.commit()
    db.session.refresh(user)
    return user

@pytest.fixture(scope='function')
def client(app):
    """创建测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """创建命令行运行器"""
    return app.test_cli_runner()

@pytest.fixture
def csrf_token(client):
    """生成CSRF令牌"""
    with client.session_transaction() as sess:
        sess['csrf_token'] = generate_csrf()
    return generate_csrf()

@pytest.fixture
def auth(client, test_user):
    """认证操作的辅助类"""
    class AuthActions:
        def __init__(self, client):
            self.client = client
            self._csrf_token = None
        
        @property
        def csrf_token(self):
            """获取CSRF令牌"""
            if not self._csrf_token:
                from flask_wtf.csrf import generate_csrf
                self._csrf_token = generate_csrf()
            return self._csrf_token
        
        def login(self, username='test', password='test', follow_redirects=False):
            """登录"""
            return self.client.post('/auth/login', data={
                'username': username,
                'password': password,
                'csrf_token': self.csrf_token,
                'remember_me': False
            }, follow_redirects=follow_redirects)
            
        def logout(self):
            """登出"""
            return self.client.post('/auth/logout', data={
                'csrf_token': self.csrf_token
            })
    
    return AuthActions(client)

@pytest.fixture(scope='session')
def init_roles(app):
    """初始化角色"""
    with app.app_context():
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
            db.session.commit()
            db.session.refresh(admin_role)
        return admin_role

@pytest.fixture(scope='function')
def authenticated_client(client, test_user, app):
    """创建一个已认证的测试客户端"""
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGE_UPLOAD_FOLDER'], exist_ok=True)

    # 确保 CSRF 保护被禁用
    app.config['WTF_CSRF_ENABLED'] = False

    # 设置会话数据
    with client.session_transaction() as sess:
        sess['_fresh'] = True
        sess['_permanent'] = True
        sess['_user_id'] = str(test_user.id)
        sess['_id'] = test_user.get_id()
        sess['user_agent'] = 'pytest'
        sess['last_active'] = datetime.now(UTC).isoformat()

    # 执行登录请求
    with app.app_context():
        with session_scope() as session:
            # 重新加载用户
            session.add(test_user)
            session.refresh(test_user)
            login_user(test_user)

            response = client.post('/auth/login', data={
                'username': 'test',
                'password': 'test'
            })

            assert response.status_code in (200, 302)

            # 添加 POST 请求方法
            def post_with_token(url, data=None, **kwargs):
                """发送 POST 请求"""
                if data is None:
                    data = {}

                # 处理文件上传
                if isinstance(data, dict) and 'file' in data:
                    form_data = MultiDict()
                    
                    # 处理文件
                    file_data = data.pop('file')
                    if isinstance(file_data, tuple):
                        stream, filename = file_data
                        file_data = FileStorage(
                            stream=stream,
                            filename=filename,
                            content_type='application/octet-stream'
                        )
                    form_data.add('file', file_data)
                    
                    # 添加其他表单数据
                    for key, value in data.items():
                        form_data.add(key, value)
                    
                    # 添加CSRF token
                    form_data.add('csrf_token', generate_csrf())
                    
                    data = form_data
                else:
                    # 如果不是文件上传，直接添加CSRF token
                    if isinstance(data, dict):
                        data = data.copy()
                    else:
                        data = MultiDict(data)
                    data['csrf_token'] = generate_csrf()

                # 在应用上下文中执行请求
                with app.app_context():
                    with session_scope() as session:
                        # 确保用户对象绑定到会话
                        current_user = session.merge(test_user)
                        return client.post(url, data=data, **kwargs)

            # 保存原始的get方法
            original_get = client.get
            
            # 添加 GET 请求方法
            def get_with_session(*args, **kwargs):
                """发送 GET 请求"""
                with app.app_context():
                    with session_scope() as session:
                        # 确保用户对象绑定到会话
                        current_user = session.merge(test_user)
                        return original_get(*args, **kwargs)

            # 替换原始的 get 方法
            client.get = get_with_session
            client.post_with_token = post_with_token

            return client

@pytest.fixture
def test_category(app, db_session):
    """创建测试分类"""
    category = Category(
        name='Test Category',
        slug='test-category',
        description='Test Category Description'
    )
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_post(app, db_session, test_user, test_category):
    """创建测试文章"""
    markdown_content = """# Test Content

This is a test post.

## Section 1
Some content in section 1.

## Section 2
Some content in section 2."""

    post = Post(
        title='Test Post',
        content=markdown_content,
        summary='Test Summary',
        author_id=test_user.id,
        category_id=test_category.id,
        status=PostStatus.PUBLISHED,
        is_private=False,
        view_count=0,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    
    # 确保 HTML 内容被正确生成
    post.html_content = markdown2.markdown(markdown_content, extras={
        'fenced-code-blocks': None,
        'tables': None,
        'header-ids': None,
        'toc': None,
        'footnotes': None,
        'metadata': None,
        'code-friendly': None
    })
    post._toc = '[]'
    
    db.session.add(post)
    db.session.commit()
    return post

@pytest.fixture
def test_tag(app, db_session):
    """创建测试标签"""
    tag = Tag(
        name='Test Tag',
        slug='test-tag',
        description='Test Tag Description'
    )
    db.session.add(tag)
    db.session.commit()
    return tag

@pytest.fixture
def test_comment(test_post, app, db_session):
    """创建测试评论"""
    comment = Comment(
        content='Test Comment',
        post_id=test_post.id,
        nickname='Test User',
        email='test@example.com',
        status=1  # 已审核
    )
    db.session.add(comment)
    db.session.commit()
    return comment