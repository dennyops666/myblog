"""merge sessions and users migrations

Revision ID: 420a050122ea
Revises: ca3764d2415a, create_sessions_table
Create Date: 2025-02-24 13:56:10.540287

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '420a050122ea'
down_revision = ('ca3764d2415a', 'create_sessions_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
