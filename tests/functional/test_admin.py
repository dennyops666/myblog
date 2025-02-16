"""
文件名：test_admin.py
描述：后台管理功能测试
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Post, Category, Tag, Comment
from app.services import PostService, CategoryService, TagService, CommentService

def test_admin_access(client, auth):
    """测试后台访问控制"""
    # 未登录时访问后台
    response = client.get('/admin/')
    assert response.status_code == 302  # 应重定向到登录页面
    
    # 登录后访问后台
    auth.login()
    response = client.get('/admin/')
    assert response.status_code == 200
    assert '管理后台'.encode() in response.data

def test_post_management(client, auth, test_post):
    """测试文章管理"""
    auth.login()
    
    # 查看文章列表
    response = client.get('/admin/posts')
    assert response.status_code == 200
    assert test_post.title.encode() in response.data
    
    # 创建新文章
    response = client.post('/admin/posts/create', data={
        'title': '新测试文章',
        'content': '这是一篇新的测试文章',
        'category_id': test_post.category_id,
        'status': 1
    })
    assert response.status_code == 302  # 应重定向到文章列表
    
    # 编辑文章
    response = client.post(f'/admin/posts/{test_post.id}/edit', data={
        'title': '更新后的文章',
        'content': test_post.content,
        'category_id': test_post.category_id,
        'status': test_post.status
    })
    assert response.status_code == 302
    
    # 删除文章
    response = client.post(f'/admin/posts/{test_post.id}/delete')
    assert response.status_code == 302

def test_category_management(client, auth, test_category):
    """测试分类管理"""
    auth.login()
    
    # 查看分类列表
    response = client.get('/admin/categories')
    assert response.status_code == 200
    assert test_category.name.encode() in response.data
    
    # 创建新分类
    response = client.post('/admin/categories/create', data={
        'name': '新测试分类',
        'description': '这是一个新的测试分类'
    })
    assert response.status_code == 302
    
    # 编辑分类
    response = client.post(f'/admin/categories/{test_category.id}/edit', data={
        'name': '更新后的分类',
        'description': test_category.description
    })
    assert response.status_code == 302
    
    # 删除分类（应该失败，因为有关联的文章）
    response = client.post(f'/admin/categories/{test_category.id}/delete')
    assert response.status_code == 302
    assert CategoryService.get_category_by_id(test_category.id) is not None

def test_tag_management(client, auth, test_tag):
    """测试标签管理"""
    auth.login()
    
    # 查看标签列表
    response = client.get('/admin/tags')
    assert response.status_code == 200
    assert test_tag.name.encode() in response.data
    
    # 创建新标签
    response = client.post('/admin/tags/create', data={
        'name': '新测试标签'
    })
    assert response.status_code == 302
    
    # 重命名标签
    response = client.post(f'/admin/tags/{test_tag.id}/rename', data={
        'name': '更新后的标签'
    })
    assert response.status_code == 302
    
    # 合并标签
    new_tag = TagService.get_tag_by_name('新测试标签')
    response = client.post('/admin/tags/merge', data={
        'source_id': new_tag.id,
        'target_id': test_tag.id
    })
    assert response.status_code == 302

def test_comment_management(client, auth, test_comment):
    """测试评论管理"""
    auth.login()
    
    # 查看评论列表
    response = client.get('/admin/comments')
    assert response.status_code == 200
    assert test_comment.content.encode() in response.data
    
    # 查看待审核评论
    response = client.get('/admin/comments?status=0')
    assert response.status_code == 200
    
    # 审核评论
    response = client.post(f'/admin/comments/{test_comment.id}/approve')
    assert response.status_code == 302
    
    # 删除评论
    response = client.post(f'/admin/comments/{test_comment.id}/delete')
    assert response.status_code == 302
    assert CommentService.get_comment_by_id(test_comment.id) is None

def test_admin_profile(client, auth):
    """测试个人资料管理"""
    auth.login()
    
    # 查看个人资料
    response = client.get('/admin/profile')
    assert response.status_code == 200
    
    # 更新个人资料
    response = client.post('/admin/profile', data={
        'email': 'new_email@example.com'
    })
    assert response.status_code == 200
    
    # 修改密码
    response = client.post('/admin/change-password', data={
        'old_password': 'password',
        'new_password': 'new_password',
        'confirm_password': 'new_password'
    })
    assert response.status_code == 302  # 应重定向到登录页面 