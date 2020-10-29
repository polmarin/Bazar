"""New User table

Revision ID: a04a2dbcd42d
Revises: e7bc47423ed1
Create Date: 2020-10-29 09:56:05.822917

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a04a2dbcd42d'
down_revision = 'e7bc47423ed1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('username', sa.String(64), nullable=False, index=True, unique=True),
        sa.Column('email', sa.String(120), nullable = False, index=True, unique=True),
        sa.Column('password_hash', sa.String(128), nullable = False)
    )


def downgrade():
    op.drop_table('user')
