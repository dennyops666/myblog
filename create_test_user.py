#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from datetime import datetime

app = create_app()

print("开始直接操作数据库创建用户...")

with app.app_context():
    # 查看现有角色
    roles = Role.query.all()
    print(f"数据库中有 {len(roles)} 个角色:")
    for role in roles:
        print(f"ID: {role.id}, 名称: {role.name}, 描述: {role.description}, 是否默认: {role.is_default}")
    
    # 查找可用角色
    available_roles = Role.query.filter(~Role.name.in_(['super_admin', 'admin', 'user'])).all()
    print(f"可用角色: {[r.name for r in available_roles]}")
    
    if not available_roles:
        print("警告: 没有可用角色!")
        exit(1)
    
    # 构建唯一用户名
    username = f"test-user-{datetime.now().strftime('%H%M%S')}"
    email = f"{username}@example.com"
    
    # 创建用户
    print(f"创建用户: {username}")
    user = User(
        username=username,
        email=email,
        nickname="测试用户",
        is_active=True
    )
    user.set_password("Test@12345")
    
    # 添加角色
    role = available_roles[0]
    user.roles.append(role)
    print(f"添加角色: {role.name}")
    
    # 保存用户
    try:
        db.session.add(user)
        db.session.commit()
        print(f"用户创建成功! ID: {user.id}")
        
        # 验证用户是否在数据库中
        saved_user = User.query.get(user.id)
        if saved_user:
            print(f"验证成功: 用户 {saved_user.username} 已存在于数据库中")
            print(f"用户ID: {saved_user.id}")
            print(f"用户名: {saved_user.username}")
            print(f"邮箱: {saved_user.email}")
            print(f"角色: {[r.name for r in saved_user.roles]}")
        else:
            print("错误: 无法在数据库中找到用户")
    except Exception as e:
        db.session.rollback()
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc() 