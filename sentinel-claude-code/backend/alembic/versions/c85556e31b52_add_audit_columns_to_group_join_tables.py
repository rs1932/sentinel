"""add audit columns to group join tables

Revision ID: c85556e31b52
Revises: 45e5719c7fbc
Create Date: 2025-08-07 21:17:17.875778

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c85556e31b52'
down_revision = '45e5719c7fbc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at and updated_at to sentinel.user_groups and sentinel.group_roles
    op.add_column('user_groups', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')), schema='sentinel')
    op.add_column('user_groups', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')), schema='sentinel')
    op.add_column('group_roles', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')), schema='sentinel')
    op.add_column('group_roles', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')), schema='sentinel')


def downgrade() -> None:
    # Remove created_at and updated_at
    op.drop_column('user_groups', 'created_at', schema='sentinel')
    op.drop_column('user_groups', 'updated_at', schema='sentinel')
    op.drop_column('group_roles', 'created_at', schema='sentinel')
    op.drop_column('group_roles', 'updated_at', schema='sentinel')