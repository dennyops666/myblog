#!/usr/bin/env python
"""
修改管理员密码的脚本
"""

from app import create_app
from app.extensions import db
from app.models.user import User

def change_password():
    """修改admin用户的密码"""
    app = create_app('development')
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        if user:
            user.set_password('admin123')
            db.session.commit()
            print('密码已成功修改为: admin123')
        else:
            print('未找到admin用户')

if __name__ == '__main__':
    change_password() 