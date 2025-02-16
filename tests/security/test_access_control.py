import pytest
from app.models import User, Post, Role, Permission
from app.services.auth import AuthService
from app.services.security import SecurityService
from app.extensions import db

@pytest.fixture
def auth_service():
    return AuthService()

@pytest.fixture
def security_service():
    return SecurityService()

class TestPermissionControl:
    """权限控制测试 [ST-006]"""

    def test_role_based_access_control(self, auth_service, test_client):
        """测试基于角色的访问控制"""
        # 创建测试用户和角色
        admin_role = Role(name='admin', permissions=Permission.ADMIN)
        user_role = Role(name='user', permissions=Permission.USER)
        db.session.add_all([admin_role, user_role])

        admin = User(username='admin', email='admin@example.com', role=admin_role)
        user = User(username='user', email='user@example.com', role=user_role)
        admin.set_password('admin123')
        user.set_password('user123')
        db.session.add_all([admin, user])
        db.session.commit()

        # 测试管理员访问权限
        with test_client.session_transaction() as session:
            session['user_id'] = admin.id

        admin_endpoints = [
            '/admin/users',
            '/admin/posts',
            '/admin/settings'
        ]

        for endpoint in admin_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 200

        # 测试普通用户访问限制
        with test_client.session_transaction() as session:
            session['user_id'] = user.id

        for endpoint in admin_endpoints:
            response = test_client.get(endpoint)
            assert response.status_code == 403

    def test_api_permission_control(self, auth_service, test_client):
        """测试API权限控制"""
        # 创建测试用户和文章
        user = User(username='testuser', email='test@example.com')
        user.set_password('test123')
        post = Post(title='Test Post', content='Content', author=user)
        db.session.add_all([user, post])
        db.session.commit()

        # 未认证访问
        response = test_client.post('/api/posts', json={
            'title': 'New Post',
            'content': 'Content'
        })
        assert response.status_code == 401

        # 认证后访问
        auth_headers = {'Authorization': f'Bearer {auth_service.generate_token(user)}'}
        
        # 测试资源所有者权限
        response = test_client.put(f'/api/posts/{post.id}', json={
            'title': 'Updated Post'
        }, headers=auth_headers)
        assert response.status_code == 200

        # 测试非资源所有者权限
        other_user = User(username='other', email='other@example.com')
        other_user.set_password('other123')
        db.session.add(other_user)
        db.session.commit()

        other_headers = {'Authorization': f'Bearer {auth_service.generate_token(other_user)}'}
        response = test_client.put(f'/api/posts/{post.id}', json={
            'title': 'Unauthorized Update'
        }, headers=other_headers)
        assert response.status_code == 403

    def test_operation_permission_control(self, auth_service, test_client):
        """测试操作权限控制"""
        # 创建测试用户和角色
        editor_role = Role(name='editor', permissions=Permission.EDITOR)
        viewer_role = Role(name='viewer', permissions=Permission.VIEWER)
        db.session.add_all([editor_role, viewer_role])

        editor = User(username='editor', email='editor@example.com', role=editor_role)
        viewer = User(username='viewer', email='viewer@example.com', role=viewer_role)
        editor.set_password('editor123')
        viewer.set_password('viewer123')
        db.session.add_all([editor, viewer])
        db.session.commit()

        # 测试编辑者权限
        with test_client.session_transaction() as session:
            session['user_id'] = editor.id

        edit_operations = [
            ('POST', '/posts/new'),
            ('PUT', '/posts/1/edit'),
            ('DELETE', '/posts/1')
        ]

        for method, endpoint in edit_operations:
            response = test_client.open(endpoint, method=method)
            assert response.status_code != 403

        # 测试查看者权限限制
        with test_client.session_transaction() as session:
            session['user_id'] = viewer.id

        for method, endpoint in edit_operations:
            response = test_client.open(endpoint, method=method)
            assert response.status_code == 403


class TestSensitiveDataAccess:
    """敏感数据访问控制测试 [ST-007]"""

    def test_personal_data_access_control(self, security_service, test_client):
        """测试个人数据访问控制"""
        # 创建测试用户
        user1 = User(username='user1', email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        user1.set_password('user1123')
        user2.set_password('user2123')
        db.session.add_all([user1, user2])
        db.session.commit()

        # 测试用户访问自己的个人信息
        with test_client.session_transaction() as session:
            session['user_id'] = user1.id

        response = test_client.get(f'/api/users/{user1.id}/profile')
        assert response.status_code == 200
        data = response.get_json()
        assert 'email' in data
        assert 'settings' in data

        # 测试用户访问他人的个人信息
        response = test_client.get(f'/api/users/{user2.id}/profile')
        assert response.status_code == 200
        data = response.get_json()
        assert 'email' not in data  # 敏感信息应被隐藏
        assert 'settings' not in data

    def test_sensitive_data_protection(self, security_service, test_client):
        """测试敏感数据保护"""
        # 创建测试用户和私密文章
        user = User(username='testuser', email='test@example.com')
        user.set_password('test123')
        private_post = Post(
            title='Private Post',
            content='Secret Content',
            author=user,
            is_private=True
        )
        db.session.add_all([user, private_post])
        db.session.commit()

        # 测试未登录访问
        response = test_client.get(f'/posts/{private_post.id}')
        assert response.status_code == 403

        # 测试作者访问
        with test_client.session_transaction() as session:
            session['user_id'] = user.id

        response = test_client.get(f'/posts/{private_post.id}')
        assert response.status_code == 200
        assert 'Secret Content' in response.data.decode()

        # 测试其他用户访问
        other_user = User(username='other', email='other@example.com')
        other_user.set_password('other123')
        db.session.add(other_user)
        db.session.commit()

        with test_client.session_transaction() as session:
            session['user_id'] = other_user.id

        response = test_client.get(f'/posts/{private_post.id}')
        assert response.status_code == 403

    def test_api_data_exposure_control(self, security_service, test_client):
        """测试API数据暴露控制"""
        # 创建测试用户和数据
        user = User(username='testuser', email='test@example.com')
        user.set_password('test123')
        user.phone = '1234567890'
        user.address = '123 Test St'
        db.session.add(user)
        db.session.commit()

        # 测试公开API返回
        response = test_client.get(f'/api/users/{user.id}')
        data = response.get_json()
        assert 'username' in data
        assert 'email' not in data
        assert 'phone' not in data
        assert 'address' not in data
        assert 'password_hash' not in data

        # 测试认证后的API返回
        with test_client.session_transaction() as session:
            session['user_id'] = user.id

        response = test_client.get('/api/user/profile')
        data = response.get_json()
        assert 'email' in data
        assert 'phone' in data
        assert 'address' in data
        assert 'password_hash' not in data  # 敏感信息永远不应返回 