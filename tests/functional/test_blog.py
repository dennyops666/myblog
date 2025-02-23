"""
文件名: test_blog.py
描述: 博客功能测试
作者: denny
创建日期: 2025-02-16
"""

from app.models.post import Post, PostStatus
from app.models.category import Category
from app.models.user import User
from app.extensions import db
from flask_wtf.csrf import generate_csrf
from datetime import datetime, timedelta, UTC
import markdown2

def test_index(client):
    """测试首页"""
    response = client.get('/blog/', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe9\xa6\x96\xe9\xa1\xb5' in response.data  # "首页"的UTF-8编码

def test_post_detail(client, test_post):
    """测试文章详情页"""
    response = client.get(f'/blog/post/{test_post.id}', follow_redirects=True)
    assert response.status_code == 200
    assert test_post.title.encode() in response.data

def test_prev_next_post(client, test_user):
    """测试上一篇和下一篇文章功能"""
    with client.application.app_context():
        # 创建三篇文章，时间依次递增
        post1 = Post(
            title='Post 1',
            content='Content 1',
            author_id=test_user.id,
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
            title='Post 2',
            content='Content 2',
            author_id=test_user.id,
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
            title='Post 3',
            content='Content 3',
            author_id=test_user.id,
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
        
        # 创建一篇草稿状态的文章
        draft_post = Post(
            title='Draft Post',
            content='Draft Content',
            author_id=test_user.id,
            status=PostStatus.DRAFT,
            created_at=datetime.now(UTC) - timedelta(days=1.5)
        )
        draft_post.html_content = markdown2.markdown(draft_post.content, extras={
            'fenced-code-blocks': None,
            'tables': None,
            'header-ids': None,
            'toc': None,
            'footnotes': None,
            'metadata': None,
            'code-friendly': None
        })
        draft_post._toc = '[]'
        db.session.add(draft_post)
        db.session.commit()
        
        # 测试第二篇文章的上一篇和下一篇
        response = client.get(f'/blog/post/{post2.id}')
        assert response.status_code == 200
        assert b'Post 1' in response.data  # 上一篇
        assert b'Post 3' in response.data  # 下一篇
        
        # 测试第一篇文章应该只有下一篇
        response = client.get(f'/blog/post/{post1.id}')
        assert response.status_code == 200
        assert b'Post 2' in response.data  # 下一篇
        
        # 测试最后一篇文章应该只有上一篇
        response = client.get(f'/blog/post/{post3.id}')
        assert response.status_code == 200
        assert b'Post 2' in response.data  # 上一篇
        
        # 清理测试数据
        db.session.query(Post).filter(Post.id.in_([post1.id, post2.id, post3.id, draft_post.id])).delete(synchronize_session=False)
        db.session.commit()

def test_post_with_markdown_content(client, test_user):
    # 创建一个默认分类
    default_category = Category(name='Default', slug='default')
    db.session.add(default_category)
    db.session.commit()

    # 创建一个包含Markdown内容的测试文章
    markdown_content = "# Test Title\n\nThis is a test post with markdown content."
    html_content = Post.render_markdown(markdown_content)
    print("Generated HTML content:", html_content)
    
    test_post = Post(
        title='Test Markdown Post',
        content=markdown_content,
        html_content=html_content,
        author=test_user,
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

def test_archive(client):
    """测试归档页面"""
    response = client.get('/blog/archive', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe5\xbd\x92\xe6\xa1\xa3' in response.data  # "归档"的UTF-8编码

def test_about(client):
    """测试关于页面"""
    response = client.get('/blog/about', follow_redirects=True)
    assert response.status_code == 200
    assert b'\xe5\x85\xb3\xe4\xba\x8e' in response.data  # "关于"的UTF-8编码

def test_create_comment(client, test_post):
    """测试创建评论"""
    # 获取CSRF令牌
    response = client.get(f'/blog/post/{test_post.id}', follow_redirects=True)
    assert response.status_code == 200
    csrf_token = generate_csrf()
    
    # 创建评论
    response = client.post(f'/blog/post/{test_post.id}/comment', 
        json={
            'content': 'Test Comment',
            'nickname': 'Test User',
            'email': 'test@example.com'
        },
        headers={
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf_token
        }
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['comment']['content'] == 'Test Comment'
    assert data['comment']['nickname'] == 'Test User' 