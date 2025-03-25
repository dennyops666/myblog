#!/usr/bin/env python
import sys
import os

# 确保能够导入应用模块
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.services.operation_log import operation_log_service

app = create_app()

with app.app_context():
    # 测试获取用户日志
    user_id = 2
    try:
        logs = operation_log_service.get_user_logs(user_id=user_id, per_page=5)
        print(f"成功获取用户 {user_id} 的日志，共 {len(logs)} 条")
        for log in logs:
            print(f"ID: {log.id}, 操作: {log.action}, 时间: {log.created_at}")
    except Exception as e:
        print(f"获取用户日志失败: {str(e)}") 