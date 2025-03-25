"""
初始化数据脚本
"""
from app import create_app
from app.models import db, Role, User, Permission
from werkzeug.security import generate_password_hash

app = create_app()

def init_data():
    with app.app_context():
        # 删除现有的数据
        db.session.execute(db.text('DELETE FROM user_roles'))
        User.query.delete()
        Role.query.delete()
        db.session.commit()
        
        # 创建角色
        roles = {
            'admin': {
                'name': 'admin',
                'description': '管理员',
                'permissions': Permission.ADMINISTRATOR.value
            },
            'user': {
                'name': 'user',
                'description': '普通用户',
                'permissions': Permission.USER.value
            }
        }
        
        created_roles = {}
        for role_key, role_data in roles.items():
            role = Role(**role_data)
            db.session.add(role)
            created_roles[role_key] = role
        
        db.session.commit()
        
        # 创建用户
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            is_active=True
        )
        admin.roles.append(created_roles['admin'])
        db.session.add(admin)
        
        test_user = User(
            username='test',
            email='test@example.com',
            password=generate_password_hash('test123'),
            is_active=True
        )
        test_user.roles.append(created_roles['user'])
        db.session.add(test_user)
        
        try:
            db.session.commit()
            print("数据初始化完成！")
        except Exception as e:
            db.session.rollback()
            print(f"初始化失败：{str(e)}")

if __name__ == '__main__':
    init_data() 