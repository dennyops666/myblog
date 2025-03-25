"""
重置管理员密码的脚本
"""
import sys
import os

# 将项目根目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

def reset_admin_password():
    """重置管理员密码"""
    app = create_app()
    
    with app.app_context():
        # 查找管理员用户
        admin = User.query.filter_by(username='admin').first()
        if admin:
            # 重置密码为 admin123
            admin.password = generate_password_hash('admin123')
            db.session.commit()
            print('管理员密码重置成功！')
            print('用户名：admin')
            print('新密码：admin123')
        else:
            print('管理员用户不存在')

if __name__ == '__main__':
    reset_admin_password() 