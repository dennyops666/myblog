"""
文件名：test_admin.py
描述：管理后台功能测试
作者：denny
"""

import pytest
from flask import url_for
from datetime import datetime, UTC
import uuid
from contextlib import contextmanager

from app.models import Post, Category, Tag, User, db
from app.models.post import PostStatus
from app.models.category import Category
from app.models.tag import Tag
from app.models.user import User
from app.extensions import db
from flask_login import login_user, current_user
from tests.conftest import session_scope

@pytest.fixture
def create_test_category(app):
    """创建测试分类"""
    with app.app_context():
        # 使用随机slug确保唯一性
        slug = f'test-category-{uuid.uuid4().hex[:8]}'
        category = Category.query.filter_by(name='测试分类').first()
        if not category:
            category = Category(
                name='测试分类',
                slug=slug,
                description='测试分类描述'
            )
            db.session.add(category)
            db.session.commit()
            db.session.refresh(category)
        return category

@pytest.fixture
def create_test_tag(app):
    """创建测试标签"""
    with app.app_context():
        # 使用随机slug确保唯一性
        slug = f'test-tag-{uuid.uuid4().hex[:8]}'
        tag = Tag.query.filter_by(name='测试标签').first()
        if not tag:
            tag = Tag(
                name='测试标签',
                slug=slug,
                description='测试标签描述'
            )
            db.session.add(tag)
            db.session.commit()
            db.session.refresh(tag)
        return tag

@pytest.fixture(autouse=True)
def reset_db_session():
    """在每个测试前后重置数据库会话"""
    # 测试前重置会话
    db.session.rollback()
    db.session.remove()
    yield
    # 测试后重置会话
    db.session.rollback()
    db.session.remove()

@contextmanager
def session_scope():
    """提供事务范围的会话上下文"""
    session = db.session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()

def test_admin_access(client, auth):
    """测试管理后台访问权限"""
    # 未登录时访问管理后台
    response = client.get(url_for('admin_view.index'), follow_redirects=True)
    assert response.status_code == 200
    assert '管理后台'.encode('utf-8') in response.data
    
    # 登录后访问管理后台
    auth.login()
    response = client.get(url_for('admin_view.index'))
    assert response.status_code == 200
    assert b'admin' in response.data

def test_post_management(client, auth, test_post):
    """测试文章管理功能"""
    # 先登录
    auth.login()
    
    # 访问文章管理页面
    response = client.get('/admin/post/')
    assert response.status_code == 200
    
    # 获取当前用户ID
    with session_scope() as session:
        user = session.query(User).filter_by(username='admin').first()
        user_id = user.id
    
    # 创建文章
    data = {
        'title': 'Test Post',
        'content': 'Test Content',
        'status': 'draft',
        'author_id': user_id  # 显式设置作者ID
    }
    response = client.post('/admin/post/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # 验证文章是否创建成功
    with session_scope() as session:
        post = session.query(Post).filter_by(title='Test Post').first()
        assert post is not None
        assert post.title == 'Test Post'
        assert post.content == 'Test Content'
        assert post.author_id == user_id

def test_post_update_category_and_tags(client, auth, create_test_category, create_test_tag):
    """测试文章更新分类和标签"""
    # 先登录
    auth.login()
    
    # 获取当前用户ID
    with session_scope() as session:
        user = session.query(User).filter_by(username='admin').first()
        user_id = user.id
    
    # 创建新分类
    new_category_data = {
        'name': 'New Test Category',
        'slug': 'new-test-category',
        'description': 'New Test Category Description'
    }
    response = client.post('/admin/category/create', data=new_category_data, follow_redirects=True)
    assert response.status_code == 200
    
    with session_scope() as session:
        new_category = session.query(Category).filter_by(name='New Test Category').first()
        assert new_category is not None
    
        new_tag_data = {
            'name': 'New Test Tag',
            'slug': 'new-test-tag',
            'description': 'New Test Tag Description'
        }
        response = client.post('/admin/tag/create', data=new_tag_data, follow_redirects=True)
        assert response.status_code == 200
    
        new_tag = session.query(Tag).filter_by(name='New Test Tag').first()
        assert new_tag is not None
    
        # 创建文章，使用初始分类和标签
        post_data = {
            'title': 'Test Post With Category And Tags',
            'content': 'Test Content With Category And Tags',
            'category_id': create_test_category.id,
            'status': 'draft',
            'tags': [str(create_test_tag.id)],
            'author_id': user_id  # 显式设置作者ID
        }
        response = client.post('/admin/post/create', data=post_data, follow_redirects=True)
        assert response.status_code == 200
    
        # 验证文章是否创建成功
        post = session.query(Post).filter_by(title='Test Post With Category And Tags').first()
        assert post is not None
        assert post.title == 'Test Post With Category And Tags'
        assert post.content == 'Test Content With Category And Tags'
        assert post.category_id == create_test_category.id
        assert post.author_id == user_id
        assert len(post.tags) == 1
        assert post.tags[0].id == create_test_tag.id
    
        # 更新文章，使用新分类和新标签
        update_data = {
            'title': 'Updated Test Post',
            'content': 'Updated Test Content',
            'category_id': new_category.id,
            'status': 'published',
            'tags': [str(new_tag.id)],
            'author_id': user_id  # 显式设置作者ID
        }
        response = client.post(f'/admin/post/{post.id}/edit', data=update_data, follow_redirects=True)
        assert response.status_code == 200
    
        # 验证文章是否更新成功
        updated_post = session.query(Post).get(post.id)
        assert updated_post.title == 'Updated Test Post'
        assert updated_post.content == 'Updated Test Content'
        assert updated_post.category_id == new_category.id
        assert len(updated_post.tags) == 1
        assert updated_post.tags[0].id == new_tag.id

def test_category_management(client, auth):
    """测试分类管理功能"""
    auth.login()
    
    # 创建分类，使用随机slug
    slug = f'test-category-{uuid.uuid4().hex[:8]}'
    data = {
        'name': 'Test Category',
        'slug': slug,
        'description': 'Test Category Description'
    }
    response = client.post('/admin/category/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # 验证分类创建成功
    category = Category.query.filter_by(name='Test Category').first()
    assert category is not None
    assert category.slug == slug
    
    # 编辑分类，使用新的随机slug
    new_slug = f'updated-category-{uuid.uuid4().hex[:8]}'
    data = {
        'name': 'Updated Category',
        'slug': new_slug,
        'description': 'Updated Category Description'
    }
    response = client.post(f'/admin/category/{category.id}/edit', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # 删除分类
    response = client.post(f'/admin/category/{category.id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert Category.query.filter_by(name='Updated Category').first() is None

def test_tag_management(client, auth):
    """测试标签管理功能"""
    auth.login()
    
    # 创建标签，使用随机slug
    slug = f'test-tag-{uuid.uuid4().hex[:8]}'
    data = {
        'name': 'Test Tag',
        'slug': slug,
        'description': 'Test Tag Description'
    }
    response = client.post('/admin/tag/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # 验证标签创建成功
    tag = Tag.query.filter_by(name='Test Tag').first()
    assert tag is not None
    assert tag.slug == slug
    
    # 编辑标签，使用新的随机slug
    new_slug = f'updated-tag-{uuid.uuid4().hex[:8]}'
    data = {
        'name': 'Updated Tag',
        'slug': new_slug,
        'description': 'Updated Tag Description'
    }
    response = client.post(f'/admin/tag/{tag.id}/edit', data=data, follow_redirects=True)
    assert response.status_code == 200
    
    # 删除标签
    response = client.post(f'/admin/tag/{tag.id}/delete', follow_redirects=True)
    assert response.status_code == 200
    assert Tag.query.filter_by(name='Updated Tag').first() is None

def test_user_profile(client, auth):
    """测试用户个人资料页面"""
    # 先登录
    auth.login()
    
    # 访问个人资料页面
    response = client.get('/admin/users/profile', follow_redirects=True)
    assert response.status_code == 200
    
    # 检查页面内容，只检查是否包含"管理后台"字样，不检查具体内容
    assert '管理后台'.encode('utf-8') in response.data