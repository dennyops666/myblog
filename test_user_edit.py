#!/usr/bin/env python
import sys
import os
import traceback

# 确保能够导入应用模块
sys.path.append(os.path.abspath('.'))

from app import create_app
from app.services.user import UserService
from app.services.operation_log import operation_log_service
from app.models import User, Role

app = create_app()

with app.app_context():
    try:
        user_id = 2
        # 第1步: 输出用户信息
        print("步骤1: 获取用户信息")
        user_service = UserService()
        result = user_service.get_user(user_id)
        if not result['status']:
            print(f"错误: {result.get('message', '未知错误')}")
            sys.exit(1)
        
        user = result['user']
        print(f"用户名: {user.username}")
        print(f"邮箱: {user.email}")
        print(f"状态: {'激活' if user.is_active else '未激活'}")
        
        # 第2步: 获取角色信息
        print("\n步骤2: 获取角色信息")
        roles = Role.query.filter(Role.name.notin_(['super_admin', 'admin'])).all()
        print(f"可用角色数: {len(roles)}")
        for role in roles:
            print(f"- {role.name}: {role.description}")
            
        # 第3步: 获取用户统计信息
        print("\n步骤3: 获取用户统计信息")
        try:
            # 查看是否有get_user_stats_by_id方法
            if hasattr(user_service, 'get_user_stats_by_id'):
                print("方法存在: get_user_stats_by_id")
                stats = user_service.get_user_stats_by_id(user.id)
                print(f"统计信息: {stats}")
            else:
                print("方法不存在: get_user_stats_by_id")
                
                # 直接从用户对象获取统计信息
                stats = {
                    'posts_count': len(user.posts) if hasattr(user, 'posts') else 0,
                    'comments_count': user.comments.count() if hasattr(user, 'comments') else 0,
                    'roles_count': len(user.roles) if hasattr(user, 'roles') else 0,
                    'is_active': user.is_active,
                    'last_login': getattr(user, 'last_login', None),
                    'created_at': user.created_at,
                    'updated_at': user.updated_at
                }
                print(f"从用户对象获取的统计信息: {stats}")
        except Exception as e:
            print(f"获取统计信息出错: {str(e)}")
            traceback.print_exc()
            
        # 第4步: 获取用户操作日志
        print("\n步骤4: 获取用户操作日志")
        try:
            recent_logs = operation_log_service.get_user_logs(
                user_id=user.id,
                per_page=5
            )
            
            if hasattr(recent_logs, 'total'):
                print(f"日志总数: {recent_logs.total}")
                
                if hasattr(recent_logs, 'items'):
                    print("最近的日志:")
                    for log in recent_logs.items:
                        print(f"- {log.action}: {log.details} ({log.created_at})")
                else:
                    print("日志对象没有items属性")
                    print(f"日志对象的属性: {dir(recent_logs)}")
            else:
                print("日志对象没有total属性")
                print(f"日志对象的类型: {type(recent_logs)}")
                print(f"日志对象的属性: {dir(recent_logs)}")
        except Exception as e:
            print(f"获取操作日志出错: {str(e)}")
            traceback.print_exc()
            
        # 第5步: 检查模板是否存在
        print("\n步骤5: 检查模板是否存在")
        template_path = os.path.join(app.root_path, 'templates', 'admin', 'user', 'edit.html')
        if os.path.exists(template_path):
            print(f"模板文件存在: {template_path}")
        else:
            print(f"模板文件不存在: {template_path}")
            
        # 第6步: 检查是否有代码依赖get_user_stats_by_id
        print("\n步骤6: 检查代码依赖")
        controller_path = os.path.join(app.root_path, 'controllers', 'admin', 'user.py')
        
        if os.path.exists(controller_path):
            with open(controller_path, 'r') as f:
                content = f.read()
                if 'get_user_stats_by_id' in content:
                    print("控制器代码中发现 'get_user_stats_by_id'")
                    for i, line in enumerate(content.splitlines()):
                        if 'get_user_stats_by_id' in line:
                            print(f"行 {i+1}: {line.strip()}")
                else:
                    print("控制器代码中未发现 'get_user_stats_by_id'")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc() 