"""
文件名: test_blog.py
描述: 博客功能测试
作者: denny
创建日期: 2025-02-16
"""

import pytest
import uuid
from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.user import User
from app.models.comment import Comment
from app.extensions import db

from datetime import datetime, timedelta, UTC
import markdown2

@pytest.fixture
def setup_test_data(app):
    """设置测试数据"""
    with app.app_context():
        # 创建测试用户
        user = User.query.filter_by(username='user').first()
        if not user:
            return None
            
        # 创建测试分类，使用随机slug避免唯一约束错误
        random_slug = f"test-category-{uuid.uuid4().hex[:8]}"
        category = Category(
            name=f'测试分类-{uuid.uuid4().hex[:8]}',
            slug=random_slug,
            description='测试分类描述'
        )
        db.session.add(category)
        db.session.commit()
        
        # 创建测试文章，使用随机标题避免唯一约束错误
        random_title = f"测试文章-{uuid.uuid4().hex[:8]}"
        post = Post(
            title=random_title,
            content='测试文章内容',
            html_content='<p>测试文章内容</p>',
            category=category,
            author_id=user.id,
            status=PostStatus.PUBLISHED
        )
        db.session.add(post)
        db.session.commit()
        
        # 保存ID以便在测试中使用
        post_id = post.id
        category_id = category.id
        user_id = user.id
        
        return {
            'user_id': user_id,
            'category_id': category_id,
            'post_id': post_id
        }

def test_index(client):
    """测试首页"""
    response = client.get('/blog/', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe9\xa6\x96\xe9\xa1\xb5' in response.data  # "首页"的UTF-8编码

def test_post_detail(client, app, setup_test_data):
    """测试文章详情页"""
    if not setup_test_data:
        pytest.skip("测试数据未创建成功")
    
    post_id = setup_test_data['post_id']
    
    with app.app_context():
        post = Post.query.get(post_id)
        assert post is not None
    
    response = client.get(f'/blog/post/{post_id}', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe6\xb5\x8b\xe8\xaf\x95\xe6\x96\x87\xe7\xab\xa0' in response.data  # "测试文章"的UTF-8编码

def test_prev_next_post(client, app, setup_test_data):
    """测试上一篇和下一篇文章功能"""
    if not setup_test_data:
        pytest.skip("测试数据未创建成功")
    
    user_id = setup_test_data['user_id']
    
    with app.app_context():
        # 创建三篇文章，时间依次递增
        post1 = Post(
            title=f'Post 1-{uuid.uuid4().hex[:8]}',
            content='Content 1',
            author_id=user_id,
            status=PostStatus.PUBLISHED,
            created_at=datetime.now(UTC) - timedelta(days=2)
        )
        post1.html_content = markdown2.markdown(post1.content, extras={
            'fenced-code-blocks': None,
            'tables': None,
            'header-ids': None,
            'toc': None,
            'footnotes': None,
            'metadata': None,
            'code-friendly': None
        })
        post1._toc = '[]'
        db.session.add(post1)
        db.session.commit()
        
        post2 = Post(
            title=f'Post 2-{uuid.uuid4().hex[:8]}',
            content='Content 2',
            author_id=user_id,
            status=PostStatus.PUBLISHED,
            created_at=datetime.now(UTC) - timedelta(days=1)
        )
        post2.html_content = markdown2.markdown(post2.content, extras={
            'fenced-code-blocks': None,
            'tables': None,
            'header-ids': None,
            'toc': None,
            'footnotes': None,
            'metadata': None,
            'code-friendly': None
        })
        post2._toc = '[]'
        db.session.add(post2)
        db.session.commit()
        
        post3 = Post(
            title=f'Post 3-{uuid.uuid4().hex[:8]}',
            content='Content 3',
            author_id=user_id,
            status=PostStatus.PUBLISHED,
            created_at=datetime.now(UTC)
        )
        post3.html_content = markdown2.markdown(post3.content, extras={
            'fenced-code-blocks': None,
            'tables': None,
            'header-ids': None,
            'toc': None,
            'footnotes': None,
            'metadata': None,
            'code-friendly': None
        })
        post3._toc = '[]'
        db.session.add(post3)
        db.session.commit()
        
        # 测试第二篇文章的上一篇和下一篇
        response = client.get(f'/blog/post/{post2.id}')
        assert response.status_code == 200
        
        # 检查是否有上一篇和下一篇的链接
        response_text = response.data.decode('utf-8')
        assert '/blog/post/' in response_text  # 确保有文章链接
        assert '上一篇' in response_text or '下一篇' in response_text  # 确保有导航链接
        
        # 测试第一篇文章应该只有下一篇
        response = client.get(f'/blog/post/{post1.id}')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert '/blog/post/' in response_text  # 确保有文章链接
        assert '没有上一篇' in response_text  # 没有上一篇
        
        # 测试最后一篇文章应该只有上一篇
        response = client.get(f'/blog/post/{post3.id}')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert '/blog/post/' in response_text  # 确保有文章链接
        assert '没有下一篇' in response_text  # 没有下一篇
        
        # 清理测试数据
        db.session.query(Post).filter(Post.id.in_([post1.id, post2.id, post3.id])).delete(synchronize_session=False)
        db.session.commit()

def test_post_with_markdown_content(client, app, setup_test_data):
    """测试Markdown内容的文章"""
    if not setup_test_data:
        pytest.skip("测试数据未创建成功")
    
    user_id = setup_test_data['user_id']
    
    with app.app_context():
        # 创建一个默认分类
        default_category = Category(name='Default', slug=f'default-{uuid.uuid4().hex[:8]}')
        db.session.add(default_category)
        db.session.commit()
    
        # 创建一个包含Markdown内容的测试文章
        markdown_content = "# Test Title\n\nThis is a test post with markdown content."
        html_content = Post.render_markdown(markdown_content)
        print("Generated HTML content:", html_content)
        
        test_post = Post(
            title=f'Test Markdown Post-{uuid.uuid4().hex[:8]}',
            content=markdown_content,
            html_content=html_content,
            author_id=user_id,
            category=default_category,
            status=PostStatus.PUBLISHED
        )
        db.session.add(test_post)
        db.session.commit()
    
        # 获取文章页面
        response = client.get(f'/blog/post/{test_post.id}')
        response_data = response.data.decode('utf-8')
        print("Response data:", response_data)
        
        assert response.status_code == 200
        # 检查渲染后的HTML内容是否存在于响应中
        assert '<h1 id="test-title">Test Title</h1>' in response_data
        assert 'This is a test post with markdown content.' in response_data
        
        # 清理测试数据
        db.session.delete(test_post)
        db.session.delete(default_category)
        db.session.commit()

def test_archive(client, app, setup_test_data):
    """测试归档页面"""
    if not setup_test_data:
        pytest.skip("测试数据未创建成功")
        
    response = client.get('/blog/archive', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe5\xbd\x92\xe6\xa1\xa3' in response.data  # "归档"的UTF-8编码

def test_about(client):
    """测试关于页面"""
    response = client.get('/blog/about', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe5\x85\xb3\xe4\xba\x8e' in response.data  # "关于"的UTF-8编码

def test_create_comment(client, app, setup_test_data):
    """测试创建评论"""
    if not setup_test_data:
        pytest.skip("测试数据未创建成功")
        
    post_id = setup_test_data['post_id']
    
    # 创建评论
    response = client.post(f'/blog/post/{post_id}/comment', 
        json={
            'content': 'Test Comment',
            'nickname': 'Test User',
            'email': 'test@example.com'
        },
        headers={
            'Content-Type': 'application/json'
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['comment']['content'] == 'Test Comment'
    assert data['comment']['nickname'] == 'Test User'
    
    # 清理测试数据
    with app.app_context():
        Comment.query.filter_by(content='Test Comment').delete()
        db.session.commit() 