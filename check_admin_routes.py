#!/usr/bin/env python3
from flask import Flask
from app import create_app

app = create_app()

with app.app_context():
    print("所有注册的路由:")
    for rule in app.url_map.iter_rules():
        if 'admin' in str(rule) and 'user' in str(rule):
            print(f"{rule.endpoint:<50s} {', '.join(rule.methods):<25s} {rule}") 