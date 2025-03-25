from app import create_app
from app.models import User, Role
from app.extensions import db
from datetime import datetime, UTC
app = create_app("testing")
with app.app_context():
    # 查找禁用用户
    disabled_user = User.query.filter_by(username="disabled_user").first()
    if disabled_user:
        print(f"禁用用户状态: 用户名={disabled_user.username}, 是否激活={disabled_user.is_active}")
        # 确保禁用用户的is_active属性为False
        if disabled_user.is_active:
            disabled_user.is_active = False
            db.session.commit()
            print("已将禁用用户的is_active属性设置为False")
    else:
        print("未找到禁用用户")
