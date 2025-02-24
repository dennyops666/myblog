"""创建会话表

Revision ID: create_sessions_table
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'create_sessions_table'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    """升级数据库"""
    op.create_table('sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(255), unique=True, nullable=False),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('expiry', sa.DateTime(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('csrf_token', sa.String(128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, 
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_active', sa.DateTime(), nullable=False,
                  server_default=sa.text('CURRENT_TIMESTAMP'),
                  server_onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(256), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 创建索引
    op.create_index('ix_sessions_session_id', 'sessions', ['session_id'], unique=True)
    op.create_index('ix_sessions_expiry', 'sessions', ['expiry'])
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])
    op.create_index('ix_sessions_last_active', 'sessions', ['last_active'])

def downgrade():
    """回滚数据库"""
    op.drop_index('ix_sessions_last_active', 'sessions')
    op.drop_index('ix_sessions_user_id', 'sessions')
    op.drop_index('ix_sessions_expiry', 'sessions')
    op.drop_index('ix_sessions_session_id', 'sessions')
    op.drop_table('sessions') 