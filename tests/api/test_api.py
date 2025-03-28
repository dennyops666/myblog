"""
文件名：test_api.py
描述：API测试用例
作者：denny
"""

import pytest
from flask import url_for, json
from app.models import Post, Comment
from datetime import datetime, UTC


def test_get_posts(client, test_post):
    """测试获取文章列表"""
    response = client.get('/api/posts')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'posts' in data
    assert 'total' in data
    assert 'pages' in data
    assert 'current_page' in data
    
    # 验证分页
    assert data['current_page'] == 1
    assert len(data['posts']) > 0
    
    # 验证文章数据结构
    post = data['posts'][0]
    assert 'id' in post
    assert 'title' in post
    assert 'summary' in post
    assert 'author' in post
    assert 'created_at' in post

def test_get_post_detail(client, test_post):
    """测试获取文章详情"""
    response = client.get(f'/api/posts/{test_post.id}')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['id'] == test_post.id
    assert data['title'] == test_post.title
    assert data['content'] == test_post.content
    assert data['html_content'] == test_post.html_content
    assert data['author'] == test_post.author.username
    assert 'created_at' in data
    assert 'updated_at' in data
    assert 'view_count' in data
    assert 'toc' in data

def test_get_nonexistent_post(client):
    """测试获取不存在的文章"""
    response = client.get('/api/posts/99999')
    assert response.status_code == 404

def test_create_comment(client, auth, test_post):
    """测试创建评论"""
    # 登录用户
    auth.login()
    
    # 创建评论
    response = client.post(
        f'/api/posts/{test_post.id}/comments',
        json={'content': '测试评论内容'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['content'] == '测试评论内容'
    assert data['author'] == 'test'

def test_create_comment_without_login(client, test_post):
    """测试未登录创建评论"""
    response = client.post(
        f'/api/posts/{test_post.id}/comments',
        json={'content': '这是一条测试评论'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401

def test_get_post_comments(client, test_post, test_comment):
    """测试获取文章评论"""
    response = client.get(f'/api/posts/{test_post.id}/comments')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'comments' in data
    assert 'total' in data
    assert 'pages' in data
    assert 'current_page' in data
    
    # 验证评论数据结构
    comment = data['comments'][0]
    assert 'id' in comment
    assert 'content' in comment
    assert 'html_content' in comment
    assert 'author' in comment
    assert 'created_at' in comment

def test_search_posts(client, test_post):
    """测试搜索文章"""
    # 使用文章标题作为关键词
    response = client.get(f'/api/search?q={test_post.title}')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'posts' in data
    assert 'total' in data
    assert 'pages' in data
    assert 'current_page' in data
    
    # 验证搜索结果
    assert len(data['posts']) > 0
    assert data['posts'][0]['title'] == test_post.title

def test_get_stats(client, test_post):
    """测试获取统计信息"""
    response = client.get('/api/stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'total_posts' in data
    assert 'published_posts' in data
    assert 'draft_posts' in data
    assert data['total_posts'] > 0

def test_api_error_handlers(client, auth, test_post):
    """测试API错误处理"""
    # 登录用户
    auth.login()
    
    # 测试400错误（缺少内容）
    response = client.post(
        f'/api/posts/{test_post.id}/comments',
        json={},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    
    # 测试404错误（文章不存在）
    response = client.post(
        '/api/posts/9999/comments',
        json={'content': '测试评论'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 404

def test_api_security(client, auth, test_post):
    """测试API安全性"""
    # 测试未登录访问
    response = client.post(
        f'/api/posts/{test_post.id}/comments',
        json={'content': '测试评论'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 401
    
    # 登录后测试XSS防护
    auth.login()
    response = client.post(
        f'/api/posts/{test_post.id}/comments',
        json={'content': '<script>alert("xss")</script>'},
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert '<script>' not in data['comment']['html_content']