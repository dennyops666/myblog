"""添加超级管理员用户标记字段

Revision ID: 1cb60ac3fa12
Revises: 8fc18fbf01d0
Create Date: 2024-03-25 05:49:28.350456

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1cb60ac3fa12'
down_revision = '8fc18fbf01d0'
branch_labels = None
depends_on = None


def upgrade():
    # 添加is_admin_user字段并设置默认值为False
    op.add_column('users', sa.Column('is_admin_user', sa.Boolean(), nullable=False, server_default='0'))
    
    # 为新字段创建索引
    op.create_index(op.f('ix_users_is_admin_user'), 'users', ['is_admin_user'], unique=False)
    
    # 创建一个超级管理员用户（如果不存在）
    try:
        # 获取连接
        conn = op.get_bind()
        
        # 检查是否已存在超级管理员用户
        admin_result = conn.execute(sa.text("SELECT id FROM users WHERE username = 'admin'")).fetchone()
        
        # 如果不存在admin用户，创建一个
        if not admin_result:
            # 创建一个新的管理员用户
            conn.execute(
                sa.text("""
                INSERT INTO users (username, email, password_hash, is_active, is_admin_user, created_at, updated_at) 
                VALUES ('admin', 'admin@example.com', 'pbkdf2:sha256:600000$XLyPTvKT1D84QeNo$ae11ffa67c941e8acecf43e2ecd6ff0136e1d5d5baab2070bfc683c12bc0fc63', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
            )
            print("已创建超级管理员用户 'admin'")
        else:
            # 如果已存在admin用户，则将其标记为超级管理员
            conn.execute(
                sa.text("UPDATE users SET is_admin_user = 1 WHERE username = 'admin'")
            )
            print("已将现有 'admin' 用户标记为超级管理员")
            
        # 检查super_admin角色是否存在
        role_result = conn.execute(sa.text("SELECT id FROM roles WHERE name = 'super_admin'")).fetchone()
        
        # 如果不存在super_admin角色，创建一个
        if not role_result:
            conn.execute(
                sa.text("""
                INSERT INTO roles (name, description, permissions, created_at, updated_at) 
                VALUES ('super_admin', '超级管理员角色', 255, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """)
            )
            role_id = conn.execute(sa.text("SELECT id FROM roles WHERE name = 'super_admin'")).fetchone()[0]
            print(f"已创建超级管理员角色 'super_admin'，ID: {role_id}")
        else:
            role_id = role_result[0]
            
        # 获取admin用户的ID
        admin_id = conn.execute(sa.text("SELECT id FROM users WHERE username = 'admin'")).fetchone()[0]
        
        # 检查admin用户是否已分配super_admin角色
        user_role_result = conn.execute(
            sa.text(f"SELECT * FROM user_roles WHERE user_id = {admin_id} AND role_id = {role_id}")
        ).fetchone()
        
        # 如果未分配，则分配super_admin角色给admin用户
        if not user_role_result:
            conn.execute(
                sa.text(f"INSERT INTO user_roles (user_id, role_id) VALUES ({admin_id}, {role_id})")
            )
            print(f"已将超级管理员角色分配给admin用户，用户ID: {admin_id}，角色ID: {role_id}")
        else:
            print("admin用户已具有超级管理员角色")
            
    except Exception as e:
        print(f"创建超级管理员用户时出错: {e}")


def downgrade():
    # 设置所有is_admin_user为0
    op.execute("UPDATE users SET is_admin_user = 0")
    
    # 删除is_admin_user字段
    op.drop_index(op.f('ix_users_is_admin_user'), table_name='users')
    op.drop_column('users', 'is_admin_user') 