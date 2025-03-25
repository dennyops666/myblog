from app import create_app
from app.models import Role
from app.extensions import db

app = create_app()
with app.app_context():
    # 打印当前角色
    print("更新前的角色列表:")
    roles = Role.query.all()
    for role in roles:
        print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}")
    
    # 修改超级管理员角色名称
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        print(f"\n找到超级管理员角色 'Admin', ID: {admin_role.id}, 权限: {admin_role.permissions}")
        admin_role.name = 'super_admin'
        print(f"正在将角色名称从 'Admin' 更改为 'super_admin'...")
        db.session.commit()
        print("已成功更新")
    else:
        print("\n没有找到名为 'Admin' 的角色")
    
    # 打印更新后的角色
    print("\n更新后的角色列表:")
    roles = Role.query.all()
    for role in roles:
        print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}") 