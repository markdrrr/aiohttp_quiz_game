"""7 migration

Revision ID: b3f08ab565ca
Revises: a5523465b26d
Create Date: 2022-03-05 23:36:01.757744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3f08ab565ca'
down_revision = 'a5523465b26d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('game', sa.Column('winner_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'game', 'user', ['winner_user_id'], ['id'], ondelete='SET NULL')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'game', type_='foreignkey')
    op.drop_column('game', 'winner_user_id')
    # ### end Alembic commands ###
