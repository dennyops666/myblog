"""
文件名：conftest.py
描述：测试配置和fixtures
作者：denny
创建日期：2024-03-21
"""

import os
import tempfile
import pytest
from datetime import datetime, UTC
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.models.post import Post
from app.models.category import Category
from app.models.tag import Tag
from app.models.comment import Comment
from app.extensions import db, csrf
from app.services.security import SecurityService
import secrets
from flask_login import login_user
from flask import session, g
from markdown import markdown
from app.utils.markdown import MarkdownService
from app.models.post import PostStatus

@pytest.fixture
def app():
    """创建并配置一个新的应用实例"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp()
    
    # 创建临时上传目录
    upload_folder = tempfile.mkdtemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': True,
        'LOGIN_DISABLED': False,
        'WTF_CSRF_CHECK_DEFAULT': True,
        'WTF_CSRF_SSL_STRICT': False,
        'API_TOKEN_HEADER': 'X-CSRF-Token',
        'SESSION_PROTECTION': 'basic',
        'SECRET_KEY': 'test_secret_key',
        'SERVER_NAME': 'localhost',
        'SESSION_COOKIE_DOMAIN': 'localhost',
        'SESSION_COOKIE_PATH': '/',
        'SESSION_COOKIE_NAME': 'session',
        'SESSION_COOKIE_SECURE': False,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SAMESITE': None,
        'PERMANENT_SESSION_LIFETIME': 3600,
        'REMEMBER_COOKIE_DURATION': 3600,
        'REMEMBER_COOKIE_SECURE': False,
        'REMEMBER_COOKIE_HTTPONLY': True,
        'REMEMBER_COOKIE_SAMESITE': None,
        'REMEMBER_COOKIE_NAME': 'remember_token',
        'REMEMBER_COOKIE_DOMAIN': 'localhost',
        'REMEMBER_COOKIE_PATH': '/',
        'UPLOAD_FOLDER': upload_folder,
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        'ALLOWED_EXTENSIONS': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'IMAGE_MAX_DIMENSION': 2048  # 最大图片尺寸
    })
    
    # 创建应用程序上下文
    with app.app_context():
        # 初始化数据库
        db.create_all()
        
        # 创建测试角色
        admin_role = Role(name='admin', description='Administrator')
        user_role = Role(name='user', description='Normal user')
        db.session.add(admin_role)
        db.session.add(user_role)
        
        # 创建测试用户
        user = User(username='test_user', email='test@example.com')
        user.set_password('password')
        user.roles.append(admin_role)  # 添加管理员角色
        user.roles.append(user_role)   # 保留普通用户角色
        db.session.add(user)
        db.session.commit()
        
        # 创建请求上下文
        with app.test_request_context():
            # 设置会话数据
            session['csrf_token'] = secrets.token_urlsafe(32)
            session['_fresh'] = True
            session['_permanent'] = True
            session['user_agent'] = 'test_agent'
            session['last_active'] = datetime.now(UTC).isoformat()
            
    yield app
    
    # 清理
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """测试客户端"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """测试CLI运行器"""
    return app.test_cli_runner()

@pytest.fixture
def csrf_token(client):
    """生成CSRF令牌"""
    with client.session_transaction() as session:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
        session['_fresh'] = True
        session['_permanent'] = True
        session['user_agent'] = 'test_agent'
        session['last_active'] = datetime.now(UTC).isoformat()
        return token

@pytest.fixture
def auth(client):
    """认证操作夹具"""
    class AuthActions:
        def __init__(self, client):
            self._client = client

        def login(self, username='test_user', password='password'):
            """登录"""
            response = self._client.get('/admin/login')
            csrf_token = response.headers.get('X-CSRF-Token')
            return self._client.post(
                '/admin/login',
                data={
                    'username': username,
                    'password': password,
                    'csrf_token': csrf_token
                },
                headers={
                    'X-CSRF-Token': csrf_token
                }
            )

        def logout(self):
            """登出"""
            response = self._client.get('/admin/login')
            csrf_token = response.headers.get('X-CSRF-Token')
            return self._client.post(
                '/admin/logout',
                data={
                    'csrf_token': csrf_token
                },
                headers={
                    'X-CSRF-Token': csrf_token
                }
            )

    return AuthActions(client)

@pytest.fixture
def test_user(app):
    """测试用户"""
    with app.app_context():
        user = User.query.filter_by(username='test_user').first()
        if not user:
            user = User(username='test_user', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
        # 设置会话数据
        with app.test_request_context():
            session['user_id'] = user.id
            session['_user_id'] = str(user.id)
            session['_fresh'] = True
            session['_permanent'] = True
            session['user_agent'] = 'test_agent'
            session['last_active'] = datetime.now(UTC).isoformat()
            session['is_authenticated'] = True
            session['csrf_token'] = secrets.token_urlsafe(32)
            login_user(user)
            
        return user

@pytest.fixture
def authenticated_client(client, auth, test_user):
    """已认证的测试客户端"""
    auth.login()
    return client

@pytest.fixture
def security_service():
    """安全服务"""
    return SecurityService()

@pytest.fixture
def test_category(app):
    """创建测试分类"""
    with app.app_context():
        category = Category.query.filter_by(name='Test Category').first()
        if not category:
            category = Category(
                name='Test Category',
                slug='test-category',
                description='This is a test category.'
            )
            db.session.add(category)
            db.session.commit()
        else:
            # 重新加载分类对象
            db.session.add(category)
            db.session.refresh(category)
        return category

@pytest.fixture
def test_post(test_user, test_category, app):
    """创建测试文章"""
    with app.app_context():
        post = Post.query.filter_by(title='Test Post').first()
        if not post:
            post = Post(
                title='Test Post',
                content='# Test Post\n\nThis is a test post.',
                category=test_category,
                author=test_user,
                status=PostStatus.PUBLISHED
            )
            db.session.add(post)
            db.session.commit()
        return post

@pytest.fixture
def test_tag(app):
    """创建测试标签"""
    with app.app_context():
        tag = Tag.query.filter_by(name='Test Tag').first()
        if not tag:
            tag = Tag(
                name='Test Tag',
                slug='test-tag'
            )
            db.session.add(tag)
            db.session.commit()
            
        return tag

@pytest.fixture
def test_comment(test_post, app):
    """创建测试评论"""
    with app.app_context():
        comment = Comment.query.filter_by(content='Test Comment').first()
        if not comment:
            comment = Comment(
                content='Test Comment',
                post=test_post,
                author_name='Test User',
                author_email='test@example.com',
                status=1
            )
            db.session.add(comment)
            db.session.commit()
            
        return comment

@pytest.fixture
def markdown_service():
    """Markdown服务"""
    return MarkdownService()