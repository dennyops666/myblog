"""
文件名：test_comment.py
描述：评论模型测试用例
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Comment, db
from app.services import CommentService, PostService

def test_comment_creation(app_context, test_comment, test_post):
    """测试评论创建"""
    assert test_comment.content == '这是一条测试评论'
    assert test_comment.post_id == test_post.id
    assert test_comment.author_name == '测试用户'
    assert test_comment.author_email == 'test@example.com'
    assert test_comment.status == 1

def test_comment_reply(app_context, test_post):
    """测试评论回复"""
    # 创建父评论
    parent_comment = CommentService.create_comment(
        content='父评论',
        post_id=test_post.id,
        author_name='父评论作者',
        author_email='parent@example.com',
        status=1
    )
    
    # 创建回复评论
    reply_comment = CommentService.create_comment(
        content='回复评论',
        post_id=test_post.id,
        author_name='回复者',
        author_email='reply@example.com',
        parent_id=parent_comment.id,
        status=1
    )
    
    assert reply_comment.parent_id == parent_comment.id
    assert parent_comment.replies.count() == 1

def test_comment_markdown_parsing(app_context, test_post):
    """测试评论Markdown解析"""
    markdown_content = """
这是一段**加粗**的文字。

- 列表项1
- 列表项2

`代码示例`
"""
    
    comment = CommentService.create_comment(
        content=markdown_content,
        post_id=test_post.id,
        author_name='测试用户',
        author_email='test@example.com',
        status=1
    )
    
    # 验证HTML内容
    assert '<strong>' in comment.html_content
    assert '<ul>' in comment.html_content
    assert '<code>' in comment.html_content

def test_comment_approval(app_context, test_post):
    """测试评论审核"""
    # 创建待审核评论
    comment = CommentService.create_comment(
        content='待审核评论',
        post_id=test_post.id,
        author_name='评论者',
        author_email='commenter@example.com',
        status=0
    )
    
    # 审核通过
    CommentService.approve_comment(comment)
    assert comment.status == 1
    
    # 获取待审核评论列表
    pending_comments = CommentService.get_pending_comments()
    assert comment not in pending_comments

def test_comment_rejection(app_context, test_post):
    """测试评论拒绝"""
    comment = CommentService.create_comment(
        content='待拒绝评论',
        post_id=test_post.id,
        author_name='评论者',
        author_email='commenter@example.com',
        status=0
    )
    
    comment_id = comment.id
    CommentService.reject_comment(comment)
    
    # 验证评论已被删除
    deleted_comment = Comment.query.get(comment_id)
    assert deleted_comment is None

def test_get_post_comments(app_context, test_post):
    """测试获取文章评论"""
    # 创建多条评论
    for i in range(3):
        CommentService.create_comment(
            content=f'评论{i}',
            post_id=test_post.id,
            author_name=f'用户{i}',
            author_email=f'user{i}@example.com',
            status=1
        )
    
    # 获取文章评论
    comments = CommentService.get_comments_by_post(test_post.id)
    assert len(comments) == 3

def test_invalid_comment_creation(app_context, test_post):
    """测试无效的评论创建"""
    # 测试内容为空
    with pytest.raises(ValueError):
        CommentService.create_comment(
            content='',
            post_id=test_post.id,
            author_name='测试用户',
            author_email='test@example.com'
        )
    
    # 测试无效的文章ID
    with pytest.raises(ValueError):
        CommentService.create_comment(
            content='评论内容',
            post_id=999,  # 不存在的文章ID
            author_name='测试用户',
            author_email='test@example.com'
        )
    
    # 测试无效的邮箱格式
    with pytest.raises(ValueError):
        CommentService.create_comment(
            content='评论内容',
            post_id=test_post.id,
            author_name='测试用户',
            author_email='invalid_email'
        ) 