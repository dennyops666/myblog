#!/usr/bin/env python
"""
创建管理员用户的脚本
"""

import os
import sys
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from datetime import datetime, UTC
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_admin():
    """创建管理员用户"""
    try:
        # 确保数据库文件存在
        db_path = '/data/myblog/instance/blog-dev.db'
        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            logger.error(f"数据库文件不存在或为空: {db_path}")
            logger.info("尝试使用SQLite直接创建数据库文件...")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # 尝试创建一个空的SQLite数据库
            import sqlite3
            try:
                conn = sqlite3.connect(db_path)
                conn.close()
                logger.info(f"成功创建空数据库文件: {db_path}")
            except Exception as e:
                logger.error(f"创建数据库文件失败: {e}")
                sys.exit(1)
        
        logger.info("初始化应用...")
        app = create_app('development')
        
        with app.app_context():
            logger.info("创建数据库表...")
            db.create_all()
            
            # 检查管理员角色是否已存在
            admin_role = Role.query.filter_by(name='Admin').first()
            if not admin_role:
                logger.info("创建管理员角色...")
                admin_role = Role(
                    name='Admin',
                    description='管理员',
                    permissions=0xff,
                    is_default=False,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                db.session.add(admin_role)
                db.session.commit()
            else:
                logger.info("管理员角色已存在")
            
            # 检查管理员用户是否已存在
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                logger.info("创建管理员用户...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    nickname='admin',
                    is_active=True,
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                
                # 分配角色
                admin.roles.append(admin_role)
                db.session.commit()
                
                logger.info('管理员用户创建成功')
                print('管理员用户创建成功')
                print('用户名: admin')
                print('密码: admin123')
            else:
                logger.info("管理员用户已存在")
                print('管理员用户已存在')
                
    except Exception as e:
        logger.error(f"创建管理员用户时发生错误: {e}", exc_info=True)
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin() 