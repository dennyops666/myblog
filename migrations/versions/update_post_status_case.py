"""Update post status values to uppercase

Revision ID: update_post_status_case
Revises: # will be filled by alembic
Create Date: 2024-03-02 08:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'update_post_status_case'
down_revision = None  # will be filled by alembic
branch_labels = None
depends_on = None

def upgrade():
    # 更新所有文章状态为大写
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE posts 
        SET status = UPPER(status)
        WHERE status IN ('draft', 'published', 'archived')
    """))

def downgrade():
    # 更新所有文章状态为小写
    conn = op.get_bind()
    conn.execute(text("""
        UPDATE posts 
        SET status = LOWER(status)
        WHERE status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')
    """)) 