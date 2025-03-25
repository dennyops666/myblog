"""
文件名：conftest.py
描述：测试配置文件
作者：denny
创建日期：2024-03-21
"""

import os
import pytest
from app import create_app
from app.extensions import db
from datetime import datetime, UTC, timedelta
from werkzeug.security import generate_password_hash
from app.models import User, Post, Category, Tag, Comment, Role
from app.models.permission import Permission
from tests.config import TestingConfig
from flask import url_for
from sqlalchemy.sql import text
from contextlib import contextmanager

@contextmanager
def session_scope():
    """提供事务范围的会话"""
    try:
        yield db.session
        db.session.commit()
    except:
        db.session.rollback()
        raise
    finally:
        db.session.remove()

@pytest.fixture(scope='session')
def app():
    """创建应用实例"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SERVER_NAME'] = 'localhost'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['WTF_CSRF_METHODS'] = []  # 禁用所有方法的CSRF保护
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    
    # 禁用重定向处理
    app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
    
    # 创建应用上下文
    with app.app_context():
        # 初始化数据库
        db.drop_all()
        db.create_all()
        
        # 初始化角色
        now = datetime.now(UTC)
        # 定义权限值
        SUPER_ADMIN = 32
        ADMIN = 16
        MODERATE = 8
        POST = 4
        COMMENT = 2
        VIEW = 1
        
        roles = [
            {
                'name': 'super_admin',
                'description': '超级管理员',
                'permissions': SUPER_ADMIN | ADMIN | MODERATE | POST | COMMENT | VIEW,  # 63
                'is_default': False
            },
            {
                'name': 'admin',
                'description': '管理员',
                'permissions': ADMIN | MODERATE | POST | COMMENT | VIEW,  # 31
                'is_default': False
            },
            {
                'name': 'editor',
                'description': '编辑者',
                'permissions': POST | COMMENT | VIEW,  # 7
                'is_default': False
            },
            {
                'name': 'user',
                'description': '普通用户',
                'permissions': COMMENT | VIEW,  # 3
                'is_default': True
            }
        ]
        
        try:
            # 创建所有角色
            for role_data in roles:
                try:
                    role = Role(
                        name=role_data['name'],
                        description=role_data['description'],
                        permissions=role_data['permissions'],
                        is_default=role_data['is_default'],
                        created_at=now,
                        updated_at=now
                    )
                    db.session.add(role)
                    db.session.flush()  # 立即执行但不提交
                    app.logger.info(f'创建角色成功: {role_data["name"]}, ID: {role.id}, 权限: {role_data["permissions"]}')
                except Exception as e:
                    app.logger.error(f'创建角色失败 {role_data["name"]}: {str(e)}')
                    db.session.rollback()
                    raise
            
            # 提交所有变更
            db.session.commit()
            
            # 验证角色初始化
            all_roles = Role.query.all()
            if len(all_roles) != len(roles):
                raise Exception(f'角色数量不匹配: 期望 {len(roles)}, 实际 {len(all_roles)}')
            
            # 验证每个角色
            for role_data in roles:
                role = Role.query.filter_by(name=role_data['name']).first()
                if not role:
                    raise Exception(f'角色未创建: {role_data["name"]}')
                if role.permissions != role_data['permissions']:
                    raise Exception(f'角色权限错误: {role_data["name"]}, 期望 {role_data["permissions"]}, 实际 {role.permissions}')
                if role.is_default != role_data['is_default']:
                    raise Exception(f'角色默认状态错误: {role_data["name"]}, 期望 {role_data["is_default"]}, 实际 {role.is_default}')
            
            app.logger.info('角色初始化成功')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'角色初始化失败: {str(e)}')
            raise
        
        # 初始化日志目录和文件
        log_dir = os.path.join(app.root_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        log_files = ['myblog.log', 'error.log', 'security.log', 'auth.log', 'db.log']
        for log_file in log_files:
            open(os.path.join(log_dir, log_file), 'a').close()
        
        # 创建测试用户
        test_users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'password123',
                'nickname': '管理员',
                'bio': '管理员账号',
                'role_names': ['admin'],
                'is_active': True
            },
            {
                'username': 'editor',
                'email': 'editor@example.com',
                'password': 'password123',
                'nickname': '编辑者',
                'bio': '编辑者账号',
                'role_names': ['editor'],
                'is_active': True
            },
            {
                'username': 'user',
                'email': 'user@example.com',
                'password': 'password123',
                'nickname': '普通用户',
                'bio': '普通用户账号',
                'role_names': ['user'],
                'is_active': True
            },
            {
                'username': 'disabled_user',
                'email': 'disabled@example.com',
                'password': 'password123',
                'nickname': '禁用用户',
                'bio': '禁用用户账号',
                'role_names': ['user'],
                'is_active': False
            },
            {
                'username': 'unverified_user',
                'email': 'unverified@example.com',
                'password': 'password123',
                'nickname': '未验证用户',
                'bio': '未验证用户账号',
                'role_names': ['user'],
                'is_active': False
            }
        ]
        
        try:
            # 创建测试用户
            for user_data in test_users:
                try:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=generate_password_hash(user_data['password']),
                        nickname=user_data['nickname'],
                        bio=user_data['bio'],
                        is_active=user_data['is_active'],
                        created_at=now,
                        updated_at=now
                    )
                    db.session.add(user)
                    db.session.flush()
                    
                    # 添加角色
                    for role_name in user_data['role_names']:
                        role = Role.query.filter_by(name=role_name).first()
                        if role:
                            user.roles.append(role)
                        else:
                            app.logger.warning(f'角色不存在: {role_name}')
                    
                    app.logger.info(f'创建用户成功: {user_data["username"]}, ID: {user.id}')
                except Exception as e:
                    app.logger.error(f'创建用户失败 {user_data["username"]}: {str(e)}')
                    db.session.rollback()
                    raise
            
            # 提交所有变更
            db.session.commit()
            
            # 验证用户初始化
            all_users = User.query.all()
            if len(all_users) != len(test_users):
                raise Exception(f'用户数量不匹配: 期望 {len(test_users)}, 实际 {len(all_users)}')
            
            # 验证每个用户
            for user_data in test_users:
                user = User.query.filter_by(username=user_data['username']).first()
                if not user:
                    raise Exception(f'用户未创建: {user_data["username"]}')
                if user.email != user_data['email']:
                    raise Exception(f'用户邮箱错误: {user_data["username"]}')
                if user.is_active != user_data['is_active']:
                    raise Exception(f'用户状态错误: {user_data["username"]}')
                if len(user.roles) != len(user_data['role_names']):
                    raise Exception(f'用户角色数量错误: {user_data["username"]}')
            
            app.logger.info('用户初始化成功')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'用户初始化失败: {str(e)}')
            raise
        
        yield app

@pytest.fixture
def client(app):
    """创建测试客户端"""
    with app.test_client() as client:
        # 禁用自动跟随重定向
        client.application.config['TESTING'] = True
        client.application.config['SERVER_NAME'] = 'localhost'
        client.application.config['WTF_CSRF_ENABLED'] = False
        client.application.config['WTF_CSRF_METHODS'] = []  # 禁用所有方法的CSRF保护
        client.application.config['WTF_CSRF_CHECK_DEFAULT'] = False
        
        # 确保不会自动跟随重定向
        client.application.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False
        
        yield client

@pytest.fixture
def runner(app):
    """创建测试命令行运行器"""
    return app.test_cli_runner()

class AuthActions:
    """认证操作类"""
    
    def __init__(self, client):
        """初始化
        
        Args:
            client: 测试客户端
        """
        self._client = client
        self._session_token = None
    
    def login(self, username='admin', password='password123', remember=True, headers=None, expect_success=True):
        """登录
        
        Args:
            username: 用户名，默认为admin
            password: 密码，默认为password123
            remember: 是否记住我，默认为True
            headers: 请求头部，用于指定请求格式
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        # 准备请求数据
        data = {
            'username': username,
            'password': password,
            'remember_me': remember
        }
    
        # 发送登录请求
        if headers and headers.get('Accept') == 'application/json':
            headers['Content-Type'] = 'application/json'
            response = self._client.post('/auth/login', json=data, headers=headers)
            
            # 检查是否期望成功
            if expect_success:
                assert response.status_code == 200
                json_data = response.get_json()
                print(f"login方法中的JSON数据: {json_data}")  # 添加打印语句
                assert json_data['status'] == 'success'
                assert json_data['message'] == '登录成功'
                assert json_data['next_url'] == url_for('dashboard.index', _external=False)
            return response
        else:
            # 表单提交
            response = self._client.post('/auth/login', data=data, follow_redirects=True)
            if expect_success:
                assert response.status_code == 200
                assert '欢迎来到仪表板' in response.get_data(as_text=True)
            return response
    
    def logout(self, headers=None):
        """登出
        
        Args:
            headers: 请求头部，用于指定请求格式
            
        Returns:
            response: 响应对象
        """
        if headers and headers.get('Accept') == 'application/json':
            headers['Content-Type'] = 'application/json'
            response = self._client.get('/auth/logout', headers=headers)
            assert response.status_code == 200
            json_data = response.get_json()
            assert json_data['status'] == 'success'
            assert json_data['message'] == '登出成功'
            assert json_data['next_url'] == url_for('auth.login', _external=False)
            return response
        else:
            response = self._client.get('/auth/logout', follow_redirects=True)
            assert response.status_code == 200
            assert b'\xe6\x88\x90\xe5\x8a\x9f\xe9\x80\x80\xe5\x87\xba\xe7\x99\xbb\xe5\xbd\x95' in response.data  # "成功退出登录"的UTF-8编码
            return response
    
    def get_session(self):
        """获取当前会话"""
        with self._client.session_transaction() as session:
            return dict(session)
    
    def clear_session(self):
        """清理会话"""
        # 清理会话数据
        with self._client.session_transaction() as session:
            session.clear()
            session.modified = True
            session.permanent = False
        
        # 重置内部状态
        self._session_token = None
        
        # 检查会话状态
        with self._client.session_transaction() as session:
            assert '_user_id' not in session
            assert '_fresh' not in session
    
    def force_logout(self, username, expect_success=True):
        """强制登出用户
        
        Args:
            username: 要登出的用户名
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        response = self._client.post('/auth/force_logout', data={
            'username': username
        })
        
        if expect_success:
            assert response.status_code == 302  # 重定向到登录页面
            assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面
            
            # 跟随重定向并检查响应
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
        
        return response
    
    def refresh_session(self, expect_success=True):
        """刷新会话
        
        Args:
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        response = self._client.get('/auth/refresh')
        
        if expect_success:
            assert response.status_code == 302  # 重定向到仪表板
            assert '/dashboard/' in response.headers['Location']  # 检查是否重定向到仪表板
            
            # 跟随重定向并检查会话
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
            session = self.get_session()
            assert 'user_id' in session
            assert session.get('session_token') != self._session_token
            self._session_token = session.get('session_token')
        
        return response
    
    def get_session_info(self):
        """获取会话信息"""
        response = self._client.get('/auth/session_info')
        assert response.status_code == 200
        return response.json
    
    def check_login_status(self):
        """检查登录状态"""
        response = self._client.get('/auth/status')
        assert response.status_code == 200
        return response.json
    
    def update_password(self, old_password, new_password, expect_success=True):
        """更新密码
        
        Args:
            old_password: 旧密码
            new_password: 新密码
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        response = self._client.post('/auth/change_password', data={
            'old_password': old_password,
            'new_password': new_password
        })
        
        if expect_success:
            assert response.status_code == 302  # 重定向到仪表板
            assert '/dashboard/' in response.headers['Location']  # 检查是否重定向到仪表板
            
            # 跟随重定向并检查响应
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
        
        return response
    
    def register(self, username, email, password, nickname=None, expect_success=True):
        """注册新用户
        
        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            nickname: 昵称，可选
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        data = {
            'username': username,
            'email': email,
            'password': password
        }
        
        if nickname:
            data['nickname'] = nickname
        
        response = self._client.post('/auth/register', data=data)
        
        if expect_success:
            assert response.status_code == 302  # 重定向到登录页面
            assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面
            
            # 跟随重定向并检查响应
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
        
        return response
    
    def reset_password_request(self, email, expect_success=True):
        """请求重置密码
        
        Args:
            email: 邮箱
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        response = self._client.post('/auth/reset_password_request', data={
            'email': email
        })
        
        if expect_success:
            assert response.status_code == 302  # 重定向到登录页面
            assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面
            
            # 跟随重定向并检查响应
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
        
        return response
    
    def reset_password(self, token, new_password, expect_success=True):
        """重置密码
        
        Args:
            token: 重置密码令牌
            new_password: 新密码
            expect_success: 是否期望操作成功
        
        Returns:
            response: 响应对象
        """
        response = self._client.post(f'/auth/reset_password/{token}', data={
            'password': new_password,
            'password2': new_password
        })
        
        if expect_success:
            assert response.status_code == 302  # 重定向到登录页面
            assert '/auth/login' in response.headers['Location']  # 检查是否重定向到登录页面
            
            # 跟随重定向并检查响应
            response = self._client.get(response.headers['Location'], follow_redirects=True)
            assert response.status_code == 200
        
        return response

@pytest.fixture
def auth(client):
    """创建认证操作实例"""
    return AuthActions(client)

@pytest.fixture
def authenticated_admin(client, auth):
    """创建已登录的管理员客户端"""
    auth.login(username='admin')
    return client

@pytest.fixture
def authenticated_client(client, auth):
    """创建已登录的客户端，用于上传测试"""
    auth.login(username='admin')
    return client

@pytest.fixture
def authenticated_editor(client, auth):
    """创建已登录的编辑者客户端"""
    auth.login(username='editor')
    return client

@pytest.fixture
def authenticated_user(client, auth):
    """创建已登录的普通用户客户端"""
    auth.login(username='user')
    return client

@pytest.fixture
def test_user(app):
    """获取或创建测试用户"""
    with app.app_context():
        return User.query.filter_by(username='user').first()

@pytest.fixture
def admin_user(app):
    """获取或创建管理员用户"""
    with app.app_context():
        return User.query.filter_by(username='admin').first()

@pytest.fixture
def editor_user(app):
    """获取或创建编辑者用户"""
    with app.app_context():
        return User.query.filter_by(username='editor').first()

@pytest.fixture
def disabled_user(app):
    """创建一个被禁用的用户"""
    with app.app_context():
        from flask import current_app
        # 检查用户是否已存在
        user = User.query.filter_by(username='disabled').first()
        if user:
            # 确保用户被禁用
            user.is_active = False
            db.session.commit()
        else:
            # 创建新的禁用用户
            user = User(
                username='disabled',
                email='disabled_test@example.com',
                password=generate_password_hash('password123'),
                is_active=False
            )
            db.session.add(user)
            db.session.commit()
        
        # 再次检查确认
        user = User.query.filter_by(username='disabled').first()
        current_app.logger.info(f"禁用用户状态: 用户名={user.username}, 是否激活={user.is_active}")
        
        return user

@pytest.fixture
def init_test_users(app):
    """初始化测试用户"""
    with app.app_context():
        try:
            # 清理现有数据
            db.session.execute(text("DELETE FROM user_roles"))
            User.query.delete()
            Role.query.delete()
            db.session.commit()
            
            # 创建管理员角色
            admin_role = Role(name='admin', description='管理员')
            db.session.add(admin_role)
            
            # 创建普通用户角色
            user_role = Role(name='user', description='普通用户')
            db.session.add(user_role)
            
            db.session.flush()
            
            # 创建用户
            now = datetime.now(UTC)
            
            # 创建管理员用户
            admin = User(
                username='admin',
                email='admin@example.com',
                nickname='管理员',
                is_active=True,
                created_at=now,
                updated_at=now
            )
            admin.set_password('password123')
            admin.roles.append(admin_role)
            db.session.add(admin)
            
            # 创建普通用户
            user = User(
                username='user',
                email='user@example.com',
                nickname='普通用户',
                is_active=True,
                created_at=now,
                updated_at=now
            )
            user.set_password('password123')
            user.roles.append(user_role)
            db.session.add(user)
            
            # 创建禁用用户
            disabled_user = User(
                username='disabled_user',
                email='disabled@example.com',
                nickname='禁用用户',
                is_active=False,
                created_at=now,
                updated_at=now
            )
            disabled_user.set_password('password123')
            disabled_user.roles.append(user_role)
            db.session.add(disabled_user)
            
            db.session.commit()
            app.logger.info('测试用户初始化成功')
            
            # 重新查询用户以确保不会出现 DetachedInstanceError
            return {
                'admin': User.query.filter_by(username='admin').first(),
                'user': User.query.filter_by(username='user').first(),
                'disabled_user': User.query.filter_by(username='disabled_user').first()
            }
        except Exception as e:
            app.logger.error(f'创建测试用户失败: {str(e)}')
            db.session.rollback()
            raise

@pytest.fixture
def test_data(app, init_test_users):
    """初始化测试数据"""
    with app.app_context():
        try:
            # 创建测试分类
            category = Category(
                name='测试分类',
                description='测试分类描述',
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            db.session.add(category)
            
            # 创建测试标签
            tag = Tag(
                name='测试标签',
                description='测试标签描述',
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            db.session.add(tag)
            
            # 创建测试文章
            post = Post(
                title='测试文章',
                content='测试文章内容',
                category=category,
                author=User.query.filter_by(username='admin').first(),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            post.tags.append(tag)
            db.session.add(post)
            
            # 创建测试评论
            comment = Comment(
                content='测试评论内容',
                author=User.query.filter_by(username='user').first(),
                post=post,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            db.session.add(comment)
            
            db.session.commit()
            
            app.logger.info('测试数据初始化成功')
            
            return {
                'category': category,
                'tag': tag,
                'post': post,
                'comment': comment
            }
        except Exception as e:
            app.logger.error(f'创建测试数据失败: {str(e)}')
            db.session.rollback()
            raise

@pytest.fixture
def test_post(app):
    """获取测试文章"""
    with app.app_context():
        return Post.query.first()

@pytest.fixture
def test_category(app):
    """获取测试分类"""
    with app.app_context():
        return Category.query.first()

@pytest.fixture
def test_tag(app):
    """获取测试标签"""
    with app.app_context():
        return Tag.query.first()

@pytest.fixture
def test_comment(app):
    """获取测试评论"""
    with app.app_context():
        return Comment.query.first()

@pytest.fixture
def expired_user(app):
    """创建过期用户"""
    with app.app_context():
        # 检查是否已存在过期用户
        expired = User.query.filter_by(username='expired').first()
        if expired:
            return expired
            
        # 创建过期用户
        now = datetime.now(UTC)
        user_role = Role.query.filter_by(name='user').first()
        
        expired = User(
            username='expired',
            email='expired@example.com',
            nickname='过期用户',
            bio='过期用户账号',
            is_active=True,  # 账号是激活的
            created_at=now,
            updated_at=now
        )
        expired.set_password('password123')
        
        if user_role:
            expired.roles.append(user_role)
        
        db.session.add(expired)
        db.session.commit()
        
        return expired