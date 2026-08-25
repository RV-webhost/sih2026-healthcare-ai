"""merge main and M2 migrations

Revision ID: 483c8fb4f234
Revises: 9697bf33a071, df92bf2469b3
Create Date: 2026-08-26 00:10:22.843865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '483c8fb4f234'
down_revision = ('9697bf33a071', 'df92bf2469b3')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
