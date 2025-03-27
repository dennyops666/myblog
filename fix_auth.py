#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from datetime import datetime

app = create_app()

with app.app_context():
    # 确认admin用户密码
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"Admin用户: {admin.username}, ID: {admin.id}")
        if admin.verify_password('admin123'):
            print("Admin密码正确: admin123")
        else:
            print("Admin密码不正确")
        
        # 确认admin用户角色
        print("Admin角色:")
        for role in admin.roles:
            print(f"  - {role.name} (ID: {role.id})")
        
        # 列出所有角色
        all_roles = Role.query.all()
        print("\n所有角色:")
        for role in all_roles:
            print(f"  - {role.name} (ID: {role.id}, 默认: {role.is_default})")
        
        # 尝试直接创建一个测试用户
        test_username = f"test-user-{datetime.now().strftime('%H%M%S')}"
        print(f"\n尝试创建测试用户: {test_username}")
        
        try:
            # 找出可用的非超级管理员角色
            available_roles = [r for r in all_roles if r.name not in ['super_admin', 'admin', 'user']]
            if not available_roles:
                print("没有可用角色，创建一个编辑者角色")
                editor_role = Role(name='editor_test', description='测试编辑者', permissions=7, is_default=False)
                db.session.add(editor_role)
                db.session.flush()
                role_to_use = editor_role
            else:
                role_to_use = available_roles[0]
            
            # 创建用户
            new_user = User(
                username=test_username,
                email=f"{test_username}@example.com",
                nickname="测试用户",
                is_active=True
            )
            new_user.set_password('Test123456')
            
            # 添加角色
            new_user.roles.append(role_to_use)
            print(f"使用角色: {role_to_use.name}")
            
            # 保存用户
            db.session.add(new_user)
            db.session.commit()
            
            print(f"用户创建成功! ID: {new_user.id}")
            
            # 验证
            created_user = User.query.filter_by(username=test_username).first()
            if created_user:
                print(f"验证成功: 用户已存在，ID: {created_user.id}")
                print(f"用户角色: {[r.name for r in created_user.roles]}")
            else:
                print("验证失败: 用户未创建")
                
        except Exception as e:
            db.session.rollback()
            print(f"错误: {str(e)}")
            import traceback
            traceback.print_exc()
    else:
        print("找不到Admin用户") 