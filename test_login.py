#!/usr/bin/env python3
from flask import Flask, session, url_for
from app import create_app
from app.models.user import User
from app.models.role import Role
from app.extensions import db
from flask_login import login_user, current_user

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False  # 禁用CSRF保护以进行测试

# 使用测试客户端
with app.test_client() as client:
    with app.app_context():
        print("1. 检查admin用户")
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print(f"Admin用户: {admin.username}, ID: {admin.id}")
            print(f"Admin用户密码hash: {admin.password_hash[:10]}...") 
            if admin.verify_password('admin123'):
                print("Admin密码验证成功: admin123")
            else:
                print("Admin密码验证失败，尝试直接登录")
        else:
            print("无法找到admin用户")
            exit(1)
        
        print("\n2. 尝试登录")
        response = client.post('/auth/login', data={
            'username': 'admin',
            'password': 'admin123',
            'remember_me': 'y'
        }, follow_redirects=True)
        
        print(f"响应状态码: {response.status_code}")
        if response.status_code == 200:
            with client.session_transaction() as sess:
                print(f"Session中的_user_id: {sess.get('_user_id')}")
                if sess.get('_user_id'):
                    print("登录成功!")
                else:
                    print("登录失败: Session中没有用户ID")
                    print(f"响应URL: {response.request.path}")
                    if b'incorrect' in response.data or b'invalid' in response.data:
                        print("可能是密码错误")
        else:
            print(f"登录失败: 状态码 {response.status_code}")
        
        print("\n3. 尝试访问用户创建页面")
        user_create_response = client.get('/admin/user/create', follow_redirects=True)
        print(f"用户创建页面响应状态码: {user_create_response.status_code}")
        print(f"最终URL: {user_create_response.request.path}")
        
        response_text = user_create_response.data.decode('utf-8')
        if '创建用户' in response_text:
            print("页面包含'创建用户'文本，访问成功!")
        else:
            print("页面不包含'创建用户'文本")
            if 'login' in response_text.lower():
                print("被重定向到登录页面，可能是登录会话问题")
            
        # 尝试直接登录用户，绕过表单
        print("\n4. 尝试使用login_user函数直接登录")
        login_result = login_user(admin)
        print(f"直接登录结果: {login_result}")
        if current_user.is_authenticated:
            print(f"当前用户: {current_user.username}, 已认证: {current_user.is_authenticated}")
            
            # 再次尝试访问用户创建页面
            print("\n5. 再次尝试访问用户创建页面")
            direct_response = client.get('/admin/user/create', follow_redirects=True)
            print(f"直接访问状态码: {direct_response.status_code}")
            print(f"直接访问最终URL: {direct_response.request.path}")
            
            direct_response_text = direct_response.data.decode('utf-8')
            if '创建用户' in direct_response_text:
                print("成功访问用户创建页面!")
            else:
                print("仍然无法访问用户创建页面") 