#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User

app = create_app()

with app.app_context():
    # 查询admin用户
    admin = User.query.filter_by(username='admin').first()
    if admin:
        print(f"用户名: {admin.username}")
        print(f"邮箱: {admin.email}")
        print(f"是否激活: {admin.is_active}")
        print(f"是管理员: {admin.is_admin_user}")
        
        # 测试密码
        passwords_to_try = ['admin', 'password', 'admin123', 'password123', '123456']
        for pwd in passwords_to_try:
            result = admin.verify_password(pwd)
            print(f"密码 '{pwd}' 是否正确: {result}")
            
        # 输出角色信息
        print("\n用户角色:")
        for role in admin.roles:
            print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}")
    else:
        print("未找到admin用户") 