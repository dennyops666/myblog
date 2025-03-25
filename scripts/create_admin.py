"""
创建管理员用户的脚本
"""
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from werkzeug.security import generate_password_hash

def create_admin_user():
    """创建管理员用户"""
    app = create_app()
    
    with app.app_context():
        # 检查是否已存在管理员角色
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='管理员',
                permissions=['admin']  # 设置管理员权限
            )
            db.session.add(admin_role)
            db.session.commit()
        
        # 检查是否已存在管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),  # 设置默认密码
                nickname='管理员',
                is_active=True
            )
            admin.roles.append(admin_role)  # 添加管理员角色
            db.session.add(admin)
            db.session.commit()
            print('管理员用户创建成功！')
            print('用户名：admin')
            print('密码：admin123')
        else:
            print('管理员用户已存在')

if __name__ == '__main__':
    create_admin_user() 