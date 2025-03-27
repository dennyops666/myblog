#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User

app = create_app()

with app.app_context():
    print('最新10个用户:')
    users = User.query.order_by(User.id.desc()).limit(10).all()
    for user in users:
        roles = [r.name for r in user.roles]
        print(f'ID: {user.id}, 用户名: {user.username}, 邮箱: {user.email}, 状态: {user.is_active}, 角色: {roles}') 