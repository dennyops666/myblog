"""
文件名：test_user.py
描述：用户模型测试用例
作者：denny
创建日期：2025-02-16
"""

import pytest
from app.models import User, db
from app.services import UserService

def test_user_creation(app_context, test_user):
    """测试用户创建"""
    assert test_user.username == 'test'
    assert test_user.email == 'test@example.com'
    test_user.set_password('cat')
    assert test_user.password_hash is not None

def test_password_hashing(app_context):
    """测试密码哈希"""
    user = User(username='test', email='test@example.com')
    user.set_password('cat')
    assert user.password_hash is not None
    assert user.check_password('cat')
    assert not user.check_password('dog')
    with pytest.raises(AttributeError):
        user.password

def test_user_service(app_context):
    """测试用户服务"""
    # 测试创建用户
    user = UserService.create_user(
        username='test_service',
        email='test_service@example.com',
        password='password'
    )
    assert user.id is not None
    assert user.username == 'test_service'
    
    # 测试通过用户名查找
    found_user = UserService.get_user_by_username('test_service')
    assert found_user is not None
    assert found_user.id == user.id
    
    # 测试通过邮箱查找
    found_user = UserService.get_user_by_email('test_service@example.com')
    assert found_user is not None
    assert found_user.id == user.id
    
    # 测试更新用户信息
    UserService.update_user(user, email='new_email@example.com')
    assert user.email == 'new_email@example.com'

def test_invalid_user_creation(app_context):
    """测试无效的用户创建"""
    # 测试缺少必填字段
    with pytest.raises(ValueError):
        UserService.create_user(
            username='',
            email='test@example.com',
            password='password'
        )
    
    with pytest.raises(ValueError):
        UserService.create_user(
            username='test',
            email='',
            password='password'
        )

def test_duplicate_username(app_context, test_user):
    """测试重复用户名"""
    with pytest.raises(ValueError):
        UserService.create_user(
            username='test',  # 与test_user使用相同的用户名
            email='another@example.com',
            password='password'
        )

def test_duplicate_email(app_context, test_user):
    """测试重复邮箱"""
    with pytest.raises(ValueError):
        UserService.create_user(
            username='another_test',
            email='test@example.com',  # 与test_user使用相同的邮箱
            password='password'
        ) 