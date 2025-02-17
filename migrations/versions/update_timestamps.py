"""更新时间戳数据
创建日期：2025-02-17
"""

from alembic import op
import sqlalchemy as sa
from datetime import datetime, UTC
from sqlalchemy.sql import table, column

# 修订版本号
revision = '2025_02_17_update_timestamps'
down_revision = '536553f58135'  # 指向初始迁移

def upgrade():
    """升级数据库"""
    # 创建sessions表
    op.create_table('sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 更新users表
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            avatar VARCHAR(200),
            bio TEXT,
            is_active BOOLEAN,
            role_id INTEGER,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            last_login DATETIME,
            FOREIGN KEY(role_id) REFERENCES roles(id)
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO users_new 
        SELECT id, username, email, password_hash, avatar, bio, is_active, role_id,
               datetime(created_at), datetime(updated_at),
               CASE WHEN last_login IS NOT NULL 
                    THEN datetime(last_login) 
                    ELSE NULL 
               END
        FROM users
    """))
    
    conn.execute(sa.text("DROP TABLE users"))
    conn.execute(sa.text("ALTER TABLE users_new RENAME TO users"))

def downgrade():
    """回滚数据库"""
    # 删除sessions表
    op.drop_table('sessions')
    
    # 回滚users表
    conn = op.get_bind()
    conn.execute(sa.text("""
        CREATE TABLE users_old (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) NOT NULL,
            email VARCHAR(120) NOT NULL,
            password_hash VARCHAR(128) NOT NULL,
            avatar VARCHAR(200),
            bio TEXT,
            is_active BOOLEAN,
            role_id INTEGER,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            last_login DATETIME,
            FOREIGN KEY(role_id) REFERENCES roles(id)
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO users_old 
        SELECT id, username, email, password_hash, avatar, bio, is_active, role_id,
               created_at, updated_at, last_login
        FROM users
    """))
    
    conn.execute(sa.text("DROP TABLE users"))
    conn.execute(sa.text("ALTER TABLE users_old RENAME TO users")) 