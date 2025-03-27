#!/usr/bin/env python3
from flask import Flask
from app import create_app
from app.models.user import User
from app.models.role import Role

app = create_app()

with app.app_context():
    default_role = Role.query.filter_by(is_default=True).first()
    print("默认角色:", default_role.id, default_role.name if default_role else None)
    
    normal_role = Role.query.filter_by(name='normal_user').first()
    print("normal_user角色:", normal_role.id, normal_role.name if normal_role else None)
    
    all_roles = Role.query.all()
    print("所有角色:")
    for role in all_roles:
        print(f"ID: {role.id}, 名称: {role.name}, 是否默认: {role.is_default}") 