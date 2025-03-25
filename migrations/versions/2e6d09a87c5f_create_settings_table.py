"""创建站点设置表

Revision ID: 2e6d09a87c5f
Revises: 1cb60ac3fa12
Create Date: 2024-03-25 05:55:38.781246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e6d09a87c5f'
down_revision = '1cb60ac3fa12'
branch_labels = None
depends_on = None


def upgrade():
    # 创建settings表
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_key'), 'settings', ['key'], unique=True)
    
    # 插入默认设置
    op.bulk_insert(
        sa.table('settings',
            sa.column('key', sa.String(100)),
            sa.column('value', sa.Text),
            sa.column('description', sa.String(255)),
            sa.column('created_at', sa.DateTime),
            sa.column('updated_at', sa.DateTime)
        ),
        [
            {
                'key': 'site_name',
                'value': '我的博客系统',
                'description': '站点名称',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'site_description',
                'value': '一个简单的博客系统',
                'description': '站点描述',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'site_keywords',
                'value': '博客,Python,Flask',
                'description': '站点关键词',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'site_url',
                'value': 'http://localhost:5000',
                'description': '站点URL',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'admin_email',
                'value': 'admin@example.com',
                'description': '管理员邮箱',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'posts_per_page',
                'value': '10',
                'description': '每页文章数',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'allow_registration',
                'value': 'true',
                'description': '是否允许注册',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            },
            {
                'key': 'enable_comments',
                'value': 'true',
                'description': '是否启用评论',
                'created_at': sa.func.current_timestamp(),
                'updated_at': sa.func.current_timestamp()
            }
        ]
    )


def downgrade():
    # 删除settings表
    op.drop_index(op.f('ix_settings_key'), table_name='settings')
    op.drop_table('settings') 