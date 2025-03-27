#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db

app = create_app()

with app.app_context():
    # 确认所有角色
    print("现有角色：")
    roles = Role.query.all()
    for role in roles:
        print(f"ID: {role.id}, 名称: {role.name}, 默认: {role.is_default}")
    
    # 获取editor角色
    editor_role = Role.query.filter_by(name='editor').first()
    
    # 创建测试用户
    test_user = User(
        username='test-user-script',
        email='test-script@example.com',
        nickname='测试脚本用户'
    )
    test_user.set_password('Test@12345')
    test_user.is_active = True
    
    # 添加角色
    test_user.roles.append(editor_role)
    
    # 保存到数据库
    try:
        print(f"添加用户: {test_user.username}")
        db.session.add(test_user)
        db.session.commit()
        print(f"用户创建成功! ID: {test_user.id}")
        
        # 验证
        saved_user = User.query.get(test_user.id)
        if saved_user:
            print(f"验证成功: 用户 {saved_user.username} 已保存")
            print(f"用户角色: {[r.name for r in saved_user.roles]}")
        else:
            print("验证失败: 无法从数据库检索用户")
    except Exception as e:
        db.session.rollback()
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc() 