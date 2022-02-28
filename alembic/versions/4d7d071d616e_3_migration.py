"""3 migration

Revision ID: 4d7d071d616e
Revises: 05295bcedc65
Create Date: 2022-02-27 23:42:02.165382

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d7d071d616e'
down_revision = '05295bcedc65'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('games_x_users')
    op.alter_column('score', 'count',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_constraint('score_user_id_fkey', 'score', type_='foreignkey')
    op.create_foreign_key(None, 'score', 'user', ['user_id'], ['id'], ondelete='SET NULL')
    op.add_column('user', sa.Column('dt_created', sa.DateTime(), server_default='now()', nullable=True))
    op.alter_column('user', 'vk_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('user', 'name',
               existing_type=sa.VARCHAR(length=120),
               nullable=False)
    op.alter_column('user', 'is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'is_admin',
               existing_type=sa.BOOLEAN(),
               nullable=True)
    op.alter_column('user', 'name',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.alter_column('user', 'vk_id',
               existing_type=sa.VARCHAR(length=120),
               nullable=True)
    op.drop_column('user', 'dt_created')
    op.drop_constraint(None, 'score', type_='foreignkey')
    op.create_foreign_key('score_user_id_fkey', 'score', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.alter_column('score', 'count',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.create_table('games_x_users',
    sa.Column('game_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['game_id'], ['game.id'], name='games_x_users_game_id_fkey'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='games_x_users_user_id_fkey')
    )
    # ### end Alembic commands ###