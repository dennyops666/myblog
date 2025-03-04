from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.role import Role

def add_admin_role():
    app = create_app()
    with app.app_context():
        # 获取admin用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            print("未找到admin用户")
            return
            
        # 获取super_admin角色
        super_admin_role = Role.query.filter_by(name='super_admin').first()
        if not super_admin_role:
            print("未找到super_admin角色")
            return
            
        # 清除现有角色
        admin_user.roles.clear()
            
        # 添加super_admin角色给用户
        admin_user.roles.append(super_admin_role)
        db.session.commit()
        print(f"已成功为用户 {admin_user.username} 添加超级管理员角色")

if __name__ == '__main__':
    add_admin_role() 