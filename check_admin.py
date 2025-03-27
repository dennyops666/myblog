#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from app.models.permission import Permission

app = create_app()

with app.app_context():
    # 查询Admin用户信息
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f'Admin用户信息：')
        print(f'ID: {admin.id}')
        print(f'用户名: {admin.username}')
        print(f'邮箱: {admin.email}')
        print(f'昵称: {admin.nickname}')
        print(f'是否活跃: {admin.is_active}')
        print(f'是否管理员: {admin.is_admin_user}')
        print(f'角色:')
        for role in admin.roles:
            print(f'- {role.name} (ID: {role.id}, 权限: {role.permissions})')
        
        # 检查是否有超级管理员权限
        has_super_admin = False
        for role in admin.roles:
            if role.permissions & Permission.SUPER_ADMIN.value:
                has_super_admin = True
                break
        
        print(f'\n超级管理员权限: {"是" if has_super_admin else "否"}')
        
        # 列出其他系统角色
        print('\n系统中所有角色:')
        roles = Role.query.all()
        for role in roles:
            users_count = db.session.query(User).join(User.roles).filter(Role.id == role.id).count()
            print(f'- {role.name} (ID: {role.id}, 权限: {role.permissions}, 用户数: {users_count})')
    else:
        print('未找到Admin用户') 