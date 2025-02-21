"""
文件名：test_admin.py
描述：管理后台功能测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from flask import url_for
from app.models import Post, Category, Tag, User
from app.models.post import PostStatus
from app.extensions import db

def test_admin_access(client):
    """测试管理后台访问权限"""
    response = client.get('/admin/')
    assert response.status_code == 401
    assert response.json['error'] == '未授权访问'

def test_post_management(client, auth, test_user):
    """测试文章管理"""
    auth.login()
    
    # 创建测试分类
    category = Category(name='Test Category', slug='test-category')
    db.session.add(category)
    db.session.commit()
    
    # 获取CSRF令牌
    response = client.get('/admin/posts')
    assert response.status_code == 200
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建文章
    response = client.post('/admin/posts/create', data={
        'title': '测试文章',
        'content': '这是一篇测试文章',
        'category_id': category.id,
        'status': 'published',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 获取文章列表
    response = client.get('/admin/posts')
    assert response.status_code == 200
    assert b'\xe6\xb5\x8b\xe8\xaf\x95\xe6\x96\x87\xe7\xab\xa0' in response.data  # '测试文章'的UTF-8编码
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 编辑文章
    post = Post.query.filter_by(title='测试文章').first()
    response = client.post(f'/admin/posts/{post.id}/edit', data={
        'title': '更新后的文章',
        'content': '这是更新后的内容',
        'category_id': category.id,
        'status': 'published',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 删除文章
    response = client.post(f'/admin/posts/{post.id}/delete', data={
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    assert not Post.query.filter_by(title='更新后的文章').first()

def test_category_management(client, auth):
    """测试分类管理"""
    auth.login()
    
    # 获取CSRF令牌
    response = client.get('/admin/categories')
    assert response.status_code == 200
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建分类
    response = client.post('/admin/categories/create', data={
        'name': '测试分类',
        'slug': 'test-category',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 获取分类列表
    response = client.get('/admin/categories')
    assert response.status_code == 200
    assert b'\xe6\xb5\x8b\xe8\xaf\x95\xe5\x88\x86\xe7\xb1\xbb' in response.data  # '测试分类'的UTF-8编码
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 编辑分类
    category = Category.query.filter_by(name='测试分类').first()
    response = client.post(f'/admin/categories/{category.id}/edit', data={
        'name': '更新后的分类',
        'slug': 'updated-category',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 删除分类
    response = client.post(f'/admin/categories/{category.id}/delete', data={
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    assert not Category.query.filter_by(name='更新后的分类').first()

def test_tag_management(client, auth):
    """测试标签管理"""
    auth.login()
    
    # 获取CSRF令牌
    response = client.get('/admin/tags')
    assert response.status_code == 200
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 创建标签
    response = client.post('/admin/tags/create', data={
        'name': '测试标签',
        'slug': 'test-tag',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 获取标签列表
    response = client.get('/admin/tags')
    assert response.status_code == 200
    assert b'\xe6\xb5\x8b\xe8\xaf\x95\xe6\xa0\x87\xe7\xad\xbe' in response.data  # '测试标签'的UTF-8编码
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 编辑标签
    tag = Tag.query.filter_by(name='测试标签').first()
    response = client.post(f'/admin/tags/{tag.id}/edit', data={
        'name': '更新后的标签',
        'slug': 'updated-tag',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    # 删除标签
    response = client.post(f'/admin/tags/{tag.id}/delete', data={
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    assert not Tag.query.filter_by(name='更新后的标签').first()

def test_admin_profile(client, auth):
    """测试管理员个人资料"""
    auth.login()
    
    # 获取个人资料页面和CSRF令牌
    response = client.get('/admin/profile')
    assert response.status_code == 200
    csrf_token = response.headers.get('X-CSRF-Token')
    
    # 更新个人资料
    response = client.post('/admin/profile', data={
        'nickname': '新昵称',
        'email': 'new@example.com',
        'csrf_token': csrf_token
    })
    assert response.status_code == 302
    
    user = User.query.filter_by(email='new@example.com').first()
    assert user.nickname == '新昵称' 