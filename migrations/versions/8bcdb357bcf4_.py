"""empty message

Revision ID: 8bcdb357bcf4
Revises: f4d46a03db23
Create Date: 2020-10-29 09:45:38.419921

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8bcdb357bcf4'
down_revision = ''
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('search', sa.Column('user', sa.INTEGER(), nullable=True))
    op.drop_constraint(None, 'search', type_='foreignkey')
    op.drop_column('search', 'user_id')
    # ### end Alembic commands ###
