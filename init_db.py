"""
文件名：init_db.py
描述：初始化数据库
作者：denny
创建日期：2024-03-21
"""

from app import create_app
from app.extensions import db
from app.models import User, Role
from app.models.permission import Permission
from datetime import datetime, UTC
import os
from config import Config
from sqlalchemy import Table, Column, Integer, String, Text, MetaData

def init_db():
    """初始化数据库"""
    app = create_app('production')
    
    # 确保目录存在
    os.makedirs(Config.INSTANCE_DIR, exist_ok=True)
    os.makedirs(Config.LOGS_DIR, exist_ok=True)
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.IMAGE_UPLOAD_FOLDER, exist_ok=True)
    
    # 确保数据库文件存在并设置权限
    db_path = os.path.join(Config.INSTANCE_DIR, 'blog-dev.db')
    if not os.path.exists(db_path):
        with open(db_path, 'w') as f:
            pass
    os.chmod(db_path, 0o777)
    
    with app.app_context():
        # 创建所有表（如果不存在）
        db.create_all()

        # 检查是否已存在角色
        if Role.query.count() == 0:
            # 创建角色
            super_admin_role = Role(
                name='super_admin',
                description='超级管理员，拥有系统的所有权限，可以管理其他管理员',
                permissions=Permission.SUPER_ADMINISTRATOR.value
            )
            admin_role = Role(
                name='admin',
                description='管理员，可以管理用户、文章、评论等内容，但不能管理其他管理员',
                permissions=Permission.ADMINISTRATOR.value
            )
            moderator_role = Role(
                name='moderator',
                description='版主，可以管理文章和评论，但不能管理用户',
                permissions=Permission.MODERATOR.value
            )
            editor_role = Role(
                name='editor',
                description='编辑，可以发布和编辑文章，但不能管理评论',
                permissions=Permission.EDITOR.value
            )
            user_role = Role(
                name='user',
                description='普通用户，可以发表评论和查看内容',
                permissions=Permission.USER.value
            )
            viewer_role = Role(
                name='viewer',
                description='访客，只能查看内容',
                permissions=Permission.VIEWER.value
            )
            
            # 添加所有角色
            for role in [super_admin_role, admin_role, moderator_role, editor_role, user_role, viewer_role]:
                db.session.add(role)
            db.session.commit()

            # 检查是否已存在超级管理员
            if not User.query.filter_by(username='admin').first():
                # 创建超级管理员用户（ID=1）
                super_admin = User(
                    id=1,
                    username='admin',
                    email='admin@example.com',
                    nickname='超级管理员',
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                super_admin.set_password('admin123')
                super_admin.roles.append(super_admin_role)
                db.session.add(super_admin)
                db.session.commit()

                print("数据库初始化完成")
                print("超级管理员账号：admin")
                print("超级管理员密码：admin123")
            else:
                print("数据库已经初始化过，跳过创建超级管理员")
        else:
            print("数据库已经初始化过，跳过创建角色")

if __name__ == '__main__':
    init_db() 