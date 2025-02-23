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
        db.session.remove()

@pytest.fixture(autouse=True)
def db_session():
    """每个测试用例自动使用的数据库会话"""
    with session_scope() as session:
        yield session

@pytest.fixture(scope='session')
def app():
    """创建Flask应用实例"""
    app = create_app('testing')
    return app

@pytest.fixture
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
    """认证操作类"""
    class AuthActions:
        def __init__(self, client):
            self._client = client

        def login(self, username='test', password='test', follow_redirects=False):
            """登录"""
            with self._client.session_transaction() as sess:
                sess['csrf_token'] = generate_csrf()
            response = self._client.post('/auth/login', 
                data={
                    'username': username,
                    'password': password,
                    'remember': True,
                    'csrf_token': generate_csrf()
                }, 
                follow_redirects=follow_redirects
            )
            
            # 设置会话变量
            with self._client.session_transaction() as sess:
                sess['_user_id'] = str(test_user.id)
                sess['_fresh'] = True
                sess['_permanent'] = True
                sess['user_agent'] = 'test'
                sess['last_active'] = datetime.now(UTC).isoformat()
                sess['is_authenticated'] = True
                sess['csrf_token'] = generate_csrf()
                sess['user'] = {
                    'id': test_user.id,
                    'username': test_user.username,
                    'email': test_user.email
                }
            
            return response

        def logout(self):
            """登出"""
            with self._client.session_transaction() as sess:
                sess['csrf_token'] = generate_csrf()
            return self._client.post('/auth/logout', data={
                'csrf_token': generate_csrf()
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
        return admin_role

@pytest.fixture
def test_user(app, db_session, init_roles):
    """创建测试用户"""
    with app.app_context():
        # 使用时间戳生成唯一的电子邮件地址
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        user = User(
            username=f'test_{timestamp}',
            email=f'test_{timestamp}@example.com'
        )
        user.set_password('test')
        
        # 添加管理员角色
        user.roles.append(init_roles)
        
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def authenticated_client(client, auth, test_user):
    """已认证的测试客户端"""
    auth.login()
    with client.session_transaction() as session:
        session['_user_id'] = test_user.id
        session['_fresh'] = True
        session['_permanent'] = True
        session['user_agent'] = 'pytest'
        session['last_active'] = datetime.now(UTC).isoformat()
        session['is_authenticated'] = True
        session['csrf_token'] = generate_csrf()
        session['user'] = {
            'id': test_user.id,
            'username': test_user.username,
            'email': test_user.email
        }
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