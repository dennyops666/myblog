#!/usr/bin/env python
"""
检查禁用用户的状态
"""

import os
from app import create_app
from app.models import User
from app.extensions import db

# 指定测试环境
app = create_app('testing')

with app.app_context():
    # 检查数据库文件是否存在
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    print(f"数据库文件路径: {db_path}")
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        
    # 检查禁用用户的状态
    disabled_user = User.query.filter_by(username='disabled_user').first()
    if disabled_user:
        print(f"禁用用户状态: 用户名={disabled_user.username}, 是否激活={disabled_user.is_active}")
        
        # 强制设置为False，不管当前状态如何
        disabled_user.is_active = False
        db.session.commit()
        print("已将禁用用户的is_active属性设置为False")
        
        # 再次检查确认
        disabled_user = User.query.filter_by(username='disabled_user').first()
        print(f"设置后的禁用用户状态: 用户名={disabled_user.username}, 是否激活={disabled_user.is_active}")
    else:
        print("禁用用户不存在，创建一个新的禁用用户")
        
        # 创建一个新的禁用用户
        disabled_user = User(
            username='disabled_user',
            email='disabled@example.com',
            nickname='禁用用户',
            is_active=False
        )
        disabled_user.set_password('password123')
        db.session.add(disabled_user)
        db.session.commit()
        
        print(f"创建禁用用户成功: 用户名={disabled_user.username}, 是否激活={disabled_user.is_active}")
