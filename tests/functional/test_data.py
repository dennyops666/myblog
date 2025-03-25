"""
文件名：test_data.py
描述：测试数据初始化
作者：denny
创建日期：2024-03-21
"""

from flask import current_app
from app.models import User, Role, db, Permission
from werkzeug.security import generate_password_hash

def init_test_data():
    """初始化测试数据"""
    # 确保在应用上下文中执行
    if not current_app:
        raise RuntimeError('必须在应用上下文中执行数据初始化')
    
    try:
        # 初始化数据库
        db.create_all()
        db.session.commit()
        
        # 清理现有数据
        Role.query.delete()
        User.query.delete()
        db.session.commit()
        
        # 创建所有角色
        roles = [
            {
                'name': 'superadmin',
                'description': '超级管理员',
                'permissions': Permission.SUPER_ADMINISTRATOR.value | Permission.ADMINISTRATOR.value | 
                              Permission.MODERATOR.value | Permission.EDITOR.value | Permission.USER.value | 
                              Permission.VIEWER.value,
                'is_default': False
            },
            {
                'name': 'admin',
                'description': '管理员',
                'permissions': Permission.ADMINISTRATOR.value | Permission.MODERATOR.value | 
                              Permission.EDITOR.value | Permission.USER.value | Permission.VIEWER.value,
                'is_default': False
            },
            {
                'name': 'moderator',
                'description': '版主',
                'permissions': Permission.MODERATOR.value | Permission.EDITOR.value | 
                              Permission.USER.value | Permission.VIEWER.value,
                'is_default': False
            },
            {
                'name': 'editor',
                'description': '编辑者',
                'permissions': Permission.EDITOR.value | Permission.USER.value | Permission.VIEWER.value,
                'is_default': False
            },
            {
                'name': 'user',
                'description': '普通用户',
                'permissions': Permission.USER.value | Permission.VIEWER.value,
                'is_default': True
            },
            {
                'name': 'viewer',
                'description': '访客',
                'permissions': Permission.VIEWER.value,
                'is_default': False
            }
        ]
        
        role_instances = {}
        for role_data in roles:
            role = Role(
                name=role_data['name'],
                description=role_data['description'],
                permissions=role_data['permissions'],
                is_default=role_data['is_default']
            )
            db.session.add(role)
            role_instances[role_data['name']] = role
        
        # 创建测试用户
        test_users = {
            'superadmin': {
                'email': 'superadmin@example.com',
                'password': 'superadmin123',
                'nickname': '超级管理员',
                'bio': '超级管理员账号',
                'role': 'superadmin'
            },
            'admin': {
                'email': 'admin@example.com',
                'password': 'admin123',
                'nickname': '管理员',
                'bio': '系统管理员账号',
                'role': 'admin'
            },
            'editor': {
                'email': 'editor@example.com',
                'password': 'editor123',
                'nickname': '编辑者',
                'bio': '编辑者账号',
                'role': 'editor'
            },
            'moderator': {
                'email': 'moderator@example.com',
                'password': 'moderator123',
                'nickname': '版主',
                'bio': '版主账号',
                'role': 'moderator'
            },
            'test': {
                'email': 'test@example.com',
                'password': 'test123',
                'nickname': '测试用户',
                'bio': '测试账号',
                'role': 'user'
            },
            'viewer': {
                'email': 'viewer@example.com',
                'password': 'viewer123',
                'nickname': '访客',
                'bio': '访客账号',
                'role': 'viewer'
            }
        }
        
        for username, user_data in test_users.items():
            user = User(
                username=username,
                email=user_data['email'],
                password=generate_password_hash(user_data['password']),
                nickname=user_data['nickname'],
                bio=user_data['bio'],
                is_active=True
            )
            user.roles.append(role_instances[user_data['role']])
            db.session.add(user)
        
        # 提交所有更改
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e