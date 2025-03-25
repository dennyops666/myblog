import pytest
from app.models import Post, Comment, User
from app.services.comment_service import CommentService
from app.services.notification import NotificationService
from app.extensions import db

@pytest.fixture
def comment_service():
    return CommentService()

@pytest.fixture
def notification_service():
    return NotificationService()

class TestCommentFunctionIntegration:
    """评论功能集成测试 [IT-005]"""

    def test_comment_creation_and_parsing(self, comment_service, test_client):
        """测试评论创建与解析"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建测试文章
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 创建带Markdown的评论
        comment_content = """This is a **markdown** comment with `code`
```python
def test():
    pass
```"""
        comment = comment_service.create_comment(
            content=comment_content,
            post_id=post.id,
            author_id=user.id
        )

        # 验证Markdown解析
        assert '<strong>markdown</strong>' in comment.html_content
        assert '<code>code</code>' in comment.html_content
        assert '<div class="highlight">' in comment.html_content
        assert '<span class="k">def</span>' in comment.html_content
        assert '<span class="k">pass</span>' in comment.html_content

    def test_article_association(self, comment_service, test_client):
        """测试文章关联"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建测试文章和评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        comment = comment_service.create_comment(
            content="Test comment",
            post_id=post.id,
            author_id=user.id
        )

        # 验证关联
        assert comment.post_id == post.id
        assert comment in post.comments
        assert post.comments_count == 1

    def test_notification_system(self, comment_service, notification_service, test_client):
        """测试通知系统"""
        # 创建测试用户和文章
        author = User(username="author", email="author@test.com")
        commenter = User(username="commenter", email="commenter@test.com")
        db.session.add_all([author, commenter])
        db.session.commit()

        post = Post(title="Test Post", content="Test content", author_id=author.id)
        db.session.add(post)
        db.session.commit()

        # 创建评论
        comment = comment_service.create_comment(
            content="Test comment",
            post_id=post.id,
            author_id=commenter.id
        )

        # 验证通知
        notifications = notification_service.get_user_notifications(author.id)
        assert len(notifications) == 1
        assert notifications[0].type == 'comment'
        assert notifications[0].target_id == comment.id

    def test_comments_count_update(self, comment_service, test_client):
        """测试评论计数更新"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建测试文章
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 创建多个评论
        for i in range(3):
            comment_service.create_comment(
                content=f"Comment {i}",
                post_id=post.id,
                author_id=user.id
            )

        # 验证计数
        assert post.comments_count == 3


class TestCommentManagementIntegration:
    """评论管理集成测试 [IT-006]"""

    def test_comment_review_process(self, comment_service, test_client):
        """测试评论审核流程"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建待审核评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        comment = comment_service.create_comment(
            content="Test comment",
            post_id=post.id,
            author_id=user.id
        )

        # 验证初始状态
        assert comment.status == 0

        # 审核通过
        comment_service.approve_comment(comment.id)
        assert comment.status == 1

    def test_status_change(self, comment_service, test_client):
        """测试状态变更"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        comment = comment_service.create_comment(
            content="Test comment",
            post_id=post.id,
            author_id=user.id
        )

        # 验证状态变更
        assert comment.status == 0
        comment_service.approve_comment(comment.id)
        assert comment.status == 1

    def test_deletion_cascade(self, comment_service, test_client):
        """测试删除级联"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # 创建文章和评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 创建父评论
        comment = comment_service.create_comment(
            content="Parent comment",
            post_id=post.id,
            author_id=user.id
        )

        # 创建回复评论
        reply = comment_service.create_comment(
            content="Reply comment",
            post_id=post.id,
            author_id=user.id,
            parent_id=comment.id
        )

        # 删除父评论
        comment_service.delete_comment(comment.id)

        # 验证父评论和回复都被删除
        assert db.session.get(Comment, comment.id) is None
        assert db.session.get(Comment, reply.id) is None

    def test_data_consistency(self, comment_service, test_client):
        """测试数据一致性"""
        # 创建测试用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        
        # 创建文章和评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 创建评论树
        parent = comment_service.create_comment(
            content="Parent comment",
            post_id=post.id,
            author_id=user.id
        )

        child1 = comment_service.create_comment(
            content="Child comment 1",
            post_id=post.id,
            author_id=user.id,
            parent_id=parent.id
        )

        child2 = comment_service.create_comment(
            content="Child comment 2",
            post_id=post.id,
            author_id=user.id,
            parent_id=parent.id
        )

        # 验证评论树结构
        assert parent.replies.count() == 2
        assert child1.parent_id == parent.id
        assert child2.parent_id == parent.id
        assert post.comments_count == 3

        # 更新评论
        comment_service.update(
            comment_id=child1.id,
            content="Updated comment"
        )

        # 验证数据一致性
        assert child1.content == "Updated comment"
        assert parent.replies.count() == 2
        assert post.comments_count == 3 