"""
文件名：test_admin.py
描述：管理后台功能测试
作者：denny
创建日期：2024-03-21
"""

import pytest
from flask import url_for
from flask_wtf.csrf import generate_csrf
from app.models import Post, Category, Tag, User, db
from app.models.post import PostStatus

def test_admin_access(client, auth):
    """测试管理后台访问权限"""
    # 未登录时访问管理后台
    response = client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200
    assert b'login' in response.data
    
    # 登录后访问管理后台
    auth.login()
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'\xe7\xae\xa1\xe7\x90\x86\xe5\x90\x8e\xe5\x8f\xb0' in response.data  # "管理后台"的UTF-8编码

def test_post_management(client, auth, test_category):
    """测试文章管理功能"""
    auth.login()
    
    # 访问文章列表页
    response = client.get('/admin/post/')
    assert response.status_code == 200
    assert '文章管理'.encode('utf-8') in response.data
    
    # 创建文章
    response = client.post('/admin/post/create', data={
        'csrf_token': generate_csrf(),
        'title': 'Test Post',
        'content': 'Test Content',
        'category_id': test_category.id,
        'status': 'draft',
        'tags': []
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 编辑文章
    post = Post.query.filter_by(title='Test Post').first()
    response = client.post(f'/admin/post/{post.id}/edit', data={
        'csrf_token': generate_csrf(),
        'title': 'Updated Post',
        'content': 'Updated Content',
        'category_id': test_category.id,
        'status': 'published',
        'tags': []
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 删除文章
    response = client.post(f'/admin/post/{post.id}/delete', data={
        'csrf_token': generate_csrf()
    }, follow_redirects=True)
    assert response.status_code == 200

def test_category_management(client, auth, test_category):
    """测试分类管理功能"""
    auth.login()
    
    # 创建分类
    response = client.post('/admin/category/create', data={
        'csrf_token': generate_csrf(),
        'name': 'New Category',
        'slug': 'new-category',
        'description': 'New Category Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 编辑分类
    category = Category.query.filter_by(name='New Category').first()
    response = client.post(f'/admin/category/{category.id}/edit', data={
        'csrf_token': generate_csrf(),
        'name': 'Updated Category',
        'slug': 'updated-category',
        'description': 'Updated Category Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 删除分类
    response = client.post(f'/admin/category/{category.id}/delete', data={
        'csrf_token': generate_csrf()
    }, follow_redirects=True)
    assert response.status_code == 200

def test_tag_management(client, auth, test_tag):
    """测试标签管理功能"""
    auth.login()
    
    # 创建标签
    response = client.post('/admin/tag/create', data={
        'csrf_token': generate_csrf(),
        'name': 'New Tag',
        'slug': 'new-tag',
        'description': 'New Tag Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 编辑标签
    tag = Tag.query.filter_by(name='New Tag').first()
    response = client.post(f'/admin/tag/{tag.id}/edit', data={
        'csrf_token': generate_csrf(),
        'name': 'Updated Tag',
        'slug': 'updated-tag',
        'description': 'Updated Tag Description'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 删除标签
    response = client.post(f'/admin/tag/{tag.id}/delete', data={
        'csrf_token': generate_csrf()
    }, follow_redirects=True)
    assert response.status_code == 200

def test_admin_profile(client, auth, test_user):
    """测试管理员个人资料"""
    # 登录
    auth.login()
    
    # 访问个人资料页面
    response = client.get('/admin/users/profile')
    assert response.status_code == 200
    assert '个人资料'.encode('utf-8') in response.data
    
    # 更新个人资料
    response = client.post('/admin/users/profile', data={
        'csrf_token': generate_csrf(),
        'username': 'updated_test',
        'email': 'updated_test@example.com'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # 验证更新是否成功
    updated_user = User.query.get(test_user.id)
    assert updated_user.username == 'updated_test'
    assert updated_user.email == 'updated_test@example.com'