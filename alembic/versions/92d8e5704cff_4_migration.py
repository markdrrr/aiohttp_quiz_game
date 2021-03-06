"""4 migration

Revision ID: 92d8e5704cff
Revises: 4d7d071d616e
Create Date: 2022-02-27 23:45:55.183262

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '92d8e5704cff'
down_revision = '4d7d071d616e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint(None, 'score', ['user_id', 'game_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'score', type_='unique')
    # ### end Alembic commands ###
