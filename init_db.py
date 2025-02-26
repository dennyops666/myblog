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

def init_db():
    """初始化数据库"""
    app = create_app('development')
    with app.app_context():
        # 创建所有表
        db.drop_all()
        db.create_all()

        # 创建角色
        super_admin_role = Role(name='super_admin', description='超级管理员', permissions=Permission.SUPER_ADMINISTRATOR.value)
        admin_role = Role(name='admin', description='管理员', permissions=Permission.ADMINISTRATOR.value)
        db.session.add(super_admin_role)
        db.session.add(admin_role)
        db.session.commit()

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

if __name__ == '__main__':
    init_db() 