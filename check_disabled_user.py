from app import create_app
from app.models import User, Role
from app.extensions import db
from datetime import datetime, UTC
app = create_app("testing")
with app.app_context():
    # 创建禁用用户
    now = datetime.now(UTC)
    user_role = Role.query.filter_by(name="user").first() or Role(name="user", description="普通用户", permissions=3, is_default=True, created_at=now, updated_at=now)
    if not user_role.id:
        db.session.add(user_role)
        db.session.flush()
    disabled_user = User.query.filter_by(username="disabled_user").first()
    if not disabled_user:
        disabled_user = User(username="disabled_user", email="disabled@example.com", nickname="禁用用户", is_active=False, created_at=now, updated_at=now)
        disabled_user.set_password("password123")
        disabled_user.roles.append(user_role)
        db.session.add(disabled_user)
        db.session.commit()
    print(f"禁用用户状态: 用户名={disabled_user.username}, 是否激活={disabled_user.is_active}")
