#!/usr/bin/env python3
from flask import Flask, url_for
from app import create_app

app = create_app()

with app.app_context():
    try:
        # 测试各种URL
        user_index_url = url_for('admin_dashboard.user.index')
        print(f"用户列表URL: {user_index_url}")
        
        # 检查蓝图注册
        print("\n注册的蓝图:")
        for blueprint_name, blueprint in app.blueprints.items():
            print(f"{blueprint_name}: {blueprint.url_prefix}")
            
        # 检查URL规则
        print("\n包含 'user' 的URL规则:")
        user_rules = [rule for rule in app.url_map.iter_rules() if 'user' in str(rule)]
        for rule in user_rules:
            print(f"{rule.endpoint}: {rule} (方法: {', '.join(rule.methods)})")
    except Exception as e:
        print(f"错误: {str(e)}") 