import pytest
from app.models import User, Post, Comment, Role
from app.services.user_service import UserService
from app.services.auth import AuthService
from app.services.log import LogService
from app.extensions import db, cache

@pytest.fixture
def user_service():
    return UserService()

@pytest.fixture
def auth_service():
    return AuthService()

@pytest.fixture
def log_service():
    return LogService()

class TestUserAuthIntegration:
    """用户认证集成测试 [IT-007]"""

    def test_login_system_integration(self, auth_service, test_client):
        """测试登录系统集成"""
        # 创建测试用户
        user = User(
            username="testuser",
            email="test@example.com"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # 测试登录
        login_result = auth_service.login(
            username="testuser",
            password="password123"
        )
        assert login_result['success']
        assert login_result['user'].id == user.id
        assert 'token' in login_result

    def test_permission_system_integration(self, auth_service, test_client):
        """测试权限系统集成"""
        # 创建角色和用户
        admin_role = Role(name="admin", permissions=["manage_users", "manage_posts"])
        editor_role = Role(name="editor", permissions=["edit_posts"])
        db.session.add_all([admin_role, editor_role])
        db.session.commit()

        admin = User(username="admin", email="admin@example.com", role_id=admin_role.id)
        editor = User(username="editor", email="editor@example.com", role_id=editor_role.id)
        db.session.add_all([admin, editor])
        db.session.commit()

        # 测试权限检查
        assert auth_service.has_permission(admin.id, "manage_users")
        assert auth_service.has_permission(editor.id, "edit_posts")
        assert not auth_service.has_permission(editor.id, "manage_users")

    def test_session_management(self, auth_service, test_client):
        """测试会话管理"""
        # 创建用户并登录
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # 登录获取token
        login_result = auth_service.login(
            username="testuser",
            password="password123"
        )
        token = login_result['token']
        
        # 验证会话
        assert auth_service.validate_session(token)
        
        # 注销
        auth_service.logout(token)
        assert not auth_service.validate_session(token)

    def test_multi_device_login(self, auth_service, test_client):
        """测试多设备登录"""
        # 创建用户
        user = User(username="testuser", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        # 模拟多设备登录
        login1 = auth_service.login(username="testuser", password="password123")
        login2 = auth_service.login(username="testuser", password="password123")
        
        # 验证所有会话
        active_sessions = auth_service.get_active_sessions(user.id)
        assert len(active_sessions) == 2

        # 注销指定设备
        auth_service.logout(login1['token'])
        active_sessions = auth_service.get_active_sessions(user.id)
        assert len(active_sessions) == 1


class TestUserDataIntegration:
    """用户数据集成测试 [IT-008]"""

    def test_user_info_association(self, user_service, test_client):
        """测试用户信息关联"""
        # 创建用户和相关数据
        user = user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        # 创建文章
        post = Post(
            title="Test Post",
            content="Test content",
            author_id=user.id
        )
        db.session.add(post)
        db.session.commit()

        # 验证用户关联
        user_posts = user_service.get_user_posts(user.id)
        assert len(user_posts) == 1
        assert user_posts[0].id == post.id
        assert user_posts[0].author_id == user.id

    def test_comment_association(self, user_service, test_client):
        """测试评论关联"""
        # 创建用户和文章
        user = user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        # 创建评论
        comment = Comment(
            content="Test comment",
            post_id=post.id,
            author_id=user.id
        )
        db.session.add(comment)
        db.session.commit()

        # 验证评论关联
        user_comments = user_service.get_user_comments(user.id)
        assert len(user_comments) == 1
        assert user_comments[0].id == comment.id
        assert user_comments[0].author_id == user.id

    def test_operation_log(self, user_service, log_service, test_client):
        """测试操作日志"""
        # 创建用户
        user = user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        # 记录各种操作
        log_service.log_action(user.id, "login", "User logged in")
        log_service.log_action(user.id, "create_post", "Created new post")
        log_service.log_action(user.id, "comment", "Posted a comment")

        # 验证日志记录
        user_logs = log_service.get_user_logs(user.id)
        assert len(user_logs) == 3
        assert "login" in [log.action for log in user_logs]
        assert "create_post" in [log.action for log in user_logs]
        assert "comment" in [log.action for log in user_logs]

    def test_data_integrity(self, user_service, test_client):
        """测试数据完整性"""
        # 创建用户和相关数据
        user = user_service.create(
            username="testuser",
            email="test@example.com",
            password="password123"
        )

        # 创建文章和评论
        post = Post(title="Test Post", content="Test content", author_id=user.id)
        db.session.add(post)
        db.session.commit()

        comment = Comment(content="Test comment", post_id=post.id, author_id=user.id)
        db.session.add(comment)
        db.session.commit()

        # 删除用户，验证级联删除
        user_service.delete(user.id)
        
        # 验证相关数据已清理
        assert Post.query.filter_by(author_id=user.id).count() == 0
        assert Comment.query.filter_by(author_id=user.id).count() == 0
        assert not auth_service.get_active_sessions(user.id)

        # 验证日志记录完整性
        deletion_log = log_service.get_system_logs()[-1]
        assert deletion_log.action == "delete_user"
        assert str(user.id) in deletion_log.details 