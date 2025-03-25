#!/usr/bin/env python
import sys
import os

# 确保能够导入应用模块
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.services.operation_log import operation_log_service
from app.services.user import UserService

app = create_app()

with app.app_context():
    user_service = UserService()
    user_id = 2
    
    try:
        print("1. 获取用户信息")
        result = user_service.get_user(user_id)
        if not result['status']:
            print(f"获取用户失败: {result.get('message', '未知错误')}")
            sys.exit(1)
            
        user = result['user']
        print(f"成功获取用户 {user.username}")
        
        print("\n2. 获取用户统计信息")
        try:
            stats = {
                'posts_count': len(user.posts) if hasattr(user, 'posts') else 0,
                'comments_count': user.comments.count() if hasattr(user, 'comments') else 0,
                'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                'is_active': user.is_active,
                'last_login': getattr(user, 'last_login', None),
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
            print(f"成功获取用户统计信息: {stats}")
        except Exception as e:
            print(f"获取用户统计信息失败: {str(e)}")
            stats = {
                'posts_count': 0,
                'comments_count': 0,
                'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                'is_active': user.is_active,
                'last_login': getattr(user, 'last_login', None),
                'created_at': user.created_at,
                'updated_at': user.updated_at
            }
            
        print("\n3. 获取用户操作日志")
        try:
            recent_logs = operation_log_service.get_user_logs(
                user_id=user.id,
                per_page=5
            )
            if hasattr(recent_logs, 'total'):
                print(f"成功获取用户操作日志，共 {recent_logs.total} 条")
                if hasattr(recent_logs, 'items'):
                    for log in recent_logs.items:
                        print(f"  - ID: {log.id}, 操作: {log.action}, 时间: {log.created_at}")
                else:
                    print("日志没有items属性")
            else:
                print("日志没有total属性")
                print(f"日志类型: {type(recent_logs)}")
                print(f"日志属性: {dir(recent_logs)}")
                
        except Exception as e:
            print(f"获取用户操作日志失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc() 