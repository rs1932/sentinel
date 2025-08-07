"""add_roles_and_user_roles_tables

Revision ID: 5d08be7e2a62
Revises: 2b6006e9e053
Create Date: 2025-08-07 09:36:54.504802

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '5d08be7e2a62'
down_revision = '2b6006e9e053'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create roles table
    op.create_table('roles',
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('system', 'custom', name='role_type', schema='sentinel'), nullable=False),
        sa.Column('parent_role_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_assignable', sa.Boolean(), nullable=True, default=True),
        sa.Column('priority', sa.Integer(), nullable=True, default=0),
        sa.Column('role_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['sentinel.users.id'], ),
        sa.ForeignKeyConstraint(['parent_role_id'], ['sentinel.roles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tenant_id'], ['sentinel.tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='sentinel'
    )
    op.create_index(op.f('ix_sentinel_roles_parent_role_id'), 'roles', ['parent_role_id'], unique=False, schema='sentinel')
    op.create_index(op.f('ix_sentinel_roles_tenant_id'), 'roles', ['tenant_id'], unique=False, schema='sentinel')
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), nullable=True, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['granted_by'], ['sentinel.users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['sentinel.roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['sentinel.users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        schema='sentinel'
    )
    op.create_index(op.f('ix_sentinel_user_roles_role_id'), 'user_roles', ['role_id'], unique=False, schema='sentinel')
    op.create_index(op.f('ix_sentinel_user_roles_user_id'), 'user_roles', ['user_id'], unique=False, schema='sentinel')
    
    # Add unique constraints
    op.create_unique_constraint('unique_role_name_per_tenant', 'roles', ['tenant_id', 'name'], schema='sentinel')
    op.create_unique_constraint('unique_user_role', 'user_roles', ['user_id', 'role_id'], schema='sentinel')


def downgrade() -> None:
    # Drop unique constraints first
    op.drop_constraint('unique_user_role', 'user_roles', schema='sentinel', type_='unique')
    op.drop_constraint('unique_role_name_per_tenant', 'roles', schema='sentinel', type_='unique')
    
    # Drop indexes
    op.drop_index(op.f('ix_sentinel_user_roles_user_id'), table_name='user_roles', schema='sentinel')
    op.drop_index(op.f('ix_sentinel_user_roles_role_id'), table_name='user_roles', schema='sentinel')
    op.drop_table('user_roles', schema='sentinel')
    
    op.drop_index(op.f('ix_sentinel_roles_tenant_id'), table_name='roles', schema='sentinel')
    op.drop_index(op.f('ix_sentinel_roles_parent_role_id'), table_name='roles', schema='sentinel')
    op.drop_table('roles', schema='sentinel')
    
    # Drop role_type enum
    op.execute("DROP TYPE IF EXISTS sentinel.role_type")