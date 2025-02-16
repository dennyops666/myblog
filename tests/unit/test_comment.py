"""
文件名：test_comment.py
描述：评论测试用例
作者：denny
创建日期：2024-03-21
"""

import pytest
from app.models import Comment, Post, User, Category, Role
from app.services.comment import CommentService
from app.extensions import db

@pytest.fixture
def test_role(app_context):
    """创建测试角色"""
    role = Role(name='user', description='普通用户')
    db.session.add(role)
    db.session.commit()
    return role

@pytest.fixture
def test_user(app_context, test_role):
    """创建测试用户"""
    user = User(username='test_user', email='test@example.com', role_id=test_role.id)
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_category(app_context):
    """创建测试分类"""
    category = Category(name='测试分类', description='这是一个测试分类')
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_post(app_context, test_user, test_category):
    """创建测试文章"""
    post = Post(
        title='Test Post',
        content='Test content',
        author_id=test_user.id,
        category_id=test_category.id
    )
    db.session.add(post)
    db.session.commit()
    return post

def test_comment_creation(app_context, test_user, test_post):
    """测试评论创建 [UT-013]"""
    # 创建普通评论
    comment = CommentService.create_comment(
        content='这是一条普通评论',
        post_id=test_post.id,
        author_id=test_user.id
    )
    
    assert comment.id is not None
    assert comment.content == '这是一条普通评论'
    assert comment.post_id == test_post.id
    assert comment.author_id == test_user.id
    assert comment.status == 0  # 默认待审核状态
    assert comment.html_content == '<p>这是一条普通评论</p>'

def test_markdown_comment_creation(app_context, test_user, test_post):
    """测试Markdown评论创建"""
    markdown_content = """
这是一条**Markdown**评论

- 列表项1
- 列表项2

```python
def test():
    print('Hello')
```
"""
    comment = CommentService.create_comment(
        content=markdown_content,
        post_id=test_post.id,
        author_id=test_user.id
    )
    
    assert comment.id is not None
    assert '<strong>Markdown</strong>' in comment.html_content
    assert '<li>列表项1</li>' in comment.html_content
    assert '<code>' in comment.html_content

def test_comment_reply(app_context, test_user, test_post):
    """测试评论回复功能"""
    # 创建父评论
    parent_comment = CommentService.create_comment(
        content='父评论',
        post_id=test_post.id,
        author_id=test_user.id
    )
    
    # 创建回复评论
    reply_comment = CommentService.create_comment(
        content='回复评论',
        post_id=test_post.id,
        author_id=test_user.id,
        parent_id=parent_comment.id
    )
    
    assert reply_comment.parent_id == parent_comment.id
    assert parent_comment.replies.count() == 1
    assert parent_comment.replies.first() == reply_comment

def test_comment_status(app_context, test_user, test_post):
    """测试评论状态"""
    # 创建评论
    comment = CommentService.create_comment(
        content='测试评论',
        post_id=test_post.id,
        author_id=test_user.id
    )
    
    # 验证初始状态
    assert comment.status == 0
    
    # 审核通过
    CommentService.approve_comment(comment.id)
    assert comment.status == 1
    
    # 拒绝评论
    CommentService.reject_comment(comment.id)
    assert Comment.query.get(comment.id) is None

def test_get_comments(app_context, test_user, test_post):
    """测试获取评论列表"""
    # 创建多个评论
    comments = []
    for i in range(3):
        comment = CommentService.create_comment(
            content=f'评论 {i}',
            post_id=test_post.id,
            author_id=test_user.id
        )
        CommentService.approve_comment(comment.id)  # 审核通过
        comments.append(comment)
    
    # 创建一个待审核评论
    pending_comment = CommentService.create_comment(
        content='待审核评论',
        post_id=test_post.id,
        author_id=test_user.id
    )
    
    # 获取已审核的评论列表
    approved_comments = CommentService.get_comments_by_post(test_post.id)
    assert len(approved_comments) == 3
    
    # 获取所有评论（包括待审核）
    all_comments = CommentService.get_comments_by_post(test_post.id, include_pending=True)
    assert len(all_comments) == 4
    
    # 获取最新评论
    recent_comments = CommentService.get_recent_comments(limit=2)
    assert len(recent_comments) == 2

def test_invalid_comment_creation(app_context, test_user, test_post):
    """测试无效的评论创建"""
    # 测试空内容
    with pytest.raises(ValueError, match='评论内容不能为空'):
        CommentService.create_comment(
            content='',
            post_id=test_post.id,
            author_id=test_user.id
        )
    
    # 测试无效的文章ID
    with pytest.raises(ValueError, match='文章不存在'):
        CommentService.create_comment(
            content='测试评论',
            post_id=999,  # 不存在的文章ID
            author_id=test_user.id
        )
    
    # 测试无效的用户ID
    with pytest.raises(ValueError, match='用户不存在'):
        CommentService.create_comment(
            content='测试评论',
            post_id=test_post.id,
            author_id=999  # 不存在的用户ID
        )
    
    # 测试无效的父评论ID
    with pytest.raises(ValueError, match='父评论不存在'):
        CommentService.create_comment(
            content='测试评论',
            post_id=test_post.id,
            author_id=test_user.id,
            parent_id=999  # 不存在的父评论ID
        ) 