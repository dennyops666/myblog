"""
文件名：test_comment.py
描述：评论测试用例
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import Comment
from app.services import CommentService

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
        author_email='parent@example.com'
    )
    
    # 创建子评论
    child_comment = CommentService.create_comment(
        content='子评论',
        post_id=test_post.id,
        author_name='子评论作者',
        author_email='child@example.com',
        parent_id=parent_comment.id
    )
    
    # 验证关系
    assert child_comment.parent_id == parent_comment.id
    assert parent_comment.replies.count() == 1
    assert parent_comment.replies.first() == child_comment

def test_comment_status(app_context, test_post):
    """测试评论状态"""
    # 创建待审核评论
    pending_comment = CommentService.create_comment(
        content='待审核评论',
        post_id=test_post.id,
        author_name='评论作者',
        author_email='author@example.com',
        status=0
    )
    
    # 验证初始状态
    assert pending_comment.status == 0
    
    # 审核通过
    CommentService.approve_comment(pending_comment)
    assert pending_comment.status == 1
    
    # 拒绝评论
    CommentService.reject_comment(pending_comment)
    assert Comment.query.get(pending_comment.id) is None

def test_get_comments(app_context, test_post):
    """测试获取评论列表"""
    # 创建多个评论
    for i in range(3):
        CommentService.create_comment(
            content=f'评论 {i}',
            post_id=test_post.id,
            author_name=f'作者 {i}',
            author_email=f'author{i}@example.com'
        )
    
    # 获取评论列表
    comments = CommentService.get_comments_by_post(test_post.id)
    assert len(comments) == 4  # 包括test_comment
    
    # 获取最新评论
    recent_comments = CommentService.get_recent_comments(limit=2)
    assert len(recent_comments) == 2

def test_invalid_comment_creation(app_context, test_post):
    """测试无效的评论创建"""
    # 测试缺少必填字段
    with pytest.raises(ValueError):
        CommentService.create_comment(
            content='',
            post_id=test_post.id,
            author_name='作者',
            author_email='author@example.com'
        )
    
    with pytest.raises(ValueError):
        CommentService.create_comment(
            content='评论内容',
            post_id=test_post.id,
            author_name='',
            author_email='author@example.com'
        ) 