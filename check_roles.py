from app import create_app
from app.models import Role
from app.models.permission import Permission
from app.extensions import db

app = create_app()
with app.app_context():
    print("所有角色:")
    roles = Role.query.all()
    for role in roles:
        print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}")
    
    print("\n超级管理员角色:")
    super_admin_roles = Role.query.filter((Role.permissions & Permission.SUPER_ADMIN) == Permission.SUPER_ADMIN).all()
    for role in super_admin_roles:
        print(f"ID: {role.id}, 名称: {role.name}, 权限: {role.permissions}")
    
    print("\n查找super_admin名称的角色:")
    super_admin_role = Role.query.filter_by(name='super_admin').first()
    if super_admin_role:
        print(f"ID: {super_admin_role.id}, 名称: {super_admin_role.name}, 权限: {super_admin_role.permissions}")
    else:
        print("没有找到名为'super_admin'的角色")
        
    # 修改角色名称
    admin_role = Role.query.filter_by(name='Admin').first()
    if admin_role:
        print(f"\n找到名为'Admin'的角色，ID: {admin_role.id}, 权限: {admin_role.permissions}")
        admin_role.name = 'super_admin'
        db.session.commit()
        print(f"已将角色名称从'Admin'更改为'super_admin'")
    else:
        print("\n没有找到名为'Admin'的角色") 