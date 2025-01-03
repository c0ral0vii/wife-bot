"""last

Revision ID: 166ac22fbadb
Revises: 
Create Date: 2024-12-29 03:07:49.134241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '166ac22fbadb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('admin_users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_users_user_id'), 'admin_users', ['user_id'], unique=True)
    op.create_table('banned_users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_banned_users_user_id'), 'banned_users', ['user_id'], unique=True)
    op.create_table('products',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('group_link', sa.String(), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('bonus', sa.Numeric(precision=25, scale=2), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('chat_id')
    )
    op.create_table('promocodes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('promo', sa.String(), nullable=False),
    sa.Column('bonus', sa.Numeric(precision=25, scale=2), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('shop',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type', sa.Enum('GLOBAL', 'LOCAL', name='shop_types'), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('users',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('status', sa.Enum('SUPER_VIP', 'MIDDLE_VIP', 'BASE_VIP', 'NOT_VIP', name='user_status'), nullable=False),
    sa.Column('vip_to', sa.Date(), nullable=True),
    sa.Column('balance', sa.Numeric(precision=25, scale=2), nullable=False),
    sa.Column('alter_balance', sa.Numeric(precision=25, scale=2), nullable=False),
    sa.Column('alter_shop_level', sa.Integer(), nullable=False),
    sa.Column('profile_imgs', sa.String(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=True)
    op.create_table('wifes',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('rare', sa.Enum('LEGENDARY', 'EPIC', 'RARE', 'SIMPLE', name='all_rares'), nullable=False),
    sa.Column('wife_imgs', sa.String(), nullable=False),
    sa.Column('from_', sa.String(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('slots',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('price', sa.Numeric(precision=25, scale=2), nullable=False),
    sa.Column('closed', sa.Boolean(), nullable=False),
    sa.Column('selled', sa.Boolean(), nullable=False),
    sa.Column('wife_id', sa.BigInteger(), nullable=False),
    sa.Column('shop_id', sa.BigInteger(), nullable=False),
    sa.Column('seller_id', sa.BigInteger(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['seller_id'], ['users.user_id'], ),
    sa.ForeignKeyConstraint(['shop_id'], ['shop.id'], ),
    sa.ForeignKeyConstraint(['wife_id'], ['wifes.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trades',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('from_id', sa.BigInteger(), nullable=False),
    sa.Column('to_id', sa.BigInteger(), nullable=False),
    sa.Column('change_from_id', sa.BigInteger(), nullable=False),
    sa.Column('change_to_id', sa.BigInteger(), nullable=True),
    sa.Column('sucess', sa.Boolean(), nullable=False),
    sa.Column('created', sa.DateTime(), nullable=False),
    sa.Column('updated', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['change_from_id'], ['wifes.id'], ),
    sa.ForeignKeyConstraint(['change_to_id'], ['wifes.id'], ),
    sa.ForeignKeyConstraint(['from_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['to_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_wife_association',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('wife_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['wife_id'], ['wifes.id'], ),
    sa.PrimaryKeyConstraint('user_id', 'wife_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_wife_association')
    op.drop_table('trades')
    op.drop_table('slots')
    op.drop_table('wifes')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')
    op.drop_table('shop')
    op.drop_table('promocodes')
    op.drop_table('products')
    op.drop_index(op.f('ix_banned_users_user_id'), table_name='banned_users')
    op.drop_table('banned_users')
    op.drop_index(op.f('ix_admin_users_user_id'), table_name='admin_users')
    op.drop_table('admin_users')
    # ### end Alembic commands ###
