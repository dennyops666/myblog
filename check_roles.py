#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.role import Role
from app.models.user import User
from app.extensions import db
from app.models.permission import Permission

app = create_app()

with app.app_context():
    # 列出所有角色
    roles = Role.query.all()
    print("系统中的角色:")
    for role in roles:
        print(f"- {role.name} (ID: {role.id}, 权限: {role.permissions}, 默认: {role.is_default})")
    
    # 检查editor角色
    editor_role = Role.query.filter_by(name='editor').first()
    if editor_role:
        print(f"\nEditor角色存在: ID={editor_role.id}, 权限={editor_role.permissions}")
        
        # 列出关联此角色的用户
        users = User.query.join(User.roles).filter(Role.id == editor_role.id).all()
        print(f"关联到Editor角色的用户数量: {len(users)}")
        for user in users:
            print(f"- {user.username} (ID: {user.id})")
    else:
        print("\nEditor角色不存在，创建它")
        try:
            new_role = Role(name='editor', description='编辑者', permissions=7)
            db.session.add(new_role)
            db.session.commit()
            print(f"创建成功: ID={new_role.id}")
        except Exception as e:
            db.session.rollback()
            print(f"创建失败: {str(e)}")
    
    # 检查admin用户是否有正确的角色
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"\nAdmin用户角色:")
        for role in admin.roles:
            print(f"- {role.name} (ID: {role.id}, 权限: {role.permissions})")

    print("\n超级管理员角色:")
    # 使用数值比较，避免使用Permission枚举进行位运算
    super_admin_value = Permission.SUPER_ADMIN.value
    super_admin_roles = Role.query.filter(Role.permissions.op('&')(super_admin_value) == super_admin_value).all()
    for role in super_admin_roles:
        print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}")
    
    print("\n查找super_admin名称的角色:")
    super_admin_role = Role.query.filter_by(name='super_admin').first()
    if super_admin_role:
        print(f"ID: {super_admin_role.id}, 名称: {super_admin_role.name}, 权限: {super_admin_role.permissions}")
    else:
        print("没有找到名为'super_admin'的角色")

    # 修改角色名称
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        print(f"\n找到名为'Admin'的角色，ID: {admin_role.id}, 权限: {admin_role.permissions}")
        admin_role.name = 'super_admin'
        db.session.commit()
        print(f"已将角色名称从'Admin'更改为'super_admin'")
    else:
        print("\n没有找到名为'Admin'的角色") 