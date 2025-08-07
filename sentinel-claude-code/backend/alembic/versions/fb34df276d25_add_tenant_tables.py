"""Add tenant tables

Revision ID: fb34df276d25
Revises: 
Create Date: 2025-08-06 15:03:14.679085

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fb34df276d25'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create sentinel schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS sentinel")
    
    # Create enum types
    op.execute("CREATE TYPE sentinel.tenant_type AS ENUM ('root', 'sub_tenant')")
    op.execute("CREATE TYPE sentinel.isolation_mode AS ENUM ('shared', 'dedicated')")
    
    # Create tenants table
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('type', postgresql.ENUM('root', 'sub_tenant', name='tenant_type', schema='sentinel'), nullable=False),
        sa.Column('parent_tenant_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('isolation_mode', postgresql.ENUM('shared', 'dedicated', name='isolation_mode', schema='sentinel'), nullable=False),
        sa.Column('settings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('features', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('tenant_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['parent_tenant_id'], ['sentinel.tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        schema='sentinel'
    )
    
    # Create indexes
    op.create_index('idx_tenants_code', 'tenants', ['code'], schema='sentinel')
    op.create_index('idx_tenants_parent_tenant_id', 'tenants', ['parent_tenant_id'], schema='sentinel')
    op.create_index('idx_tenants_is_active', 'tenants', ['is_active'], schema='sentinel')
    
    # Insert platform tenant
    op.execute("""
        INSERT INTO sentinel.tenants (
            id, name, code, type, parent_tenant_id, 
            isolation_mode, settings, features, tenant_metadata, is_active
        ) VALUES (
            '00000000-0000-0000-0000-000000000000'::uuid,
            'Sentinel Platform',
            'PLATFORM',
            'root',
            NULL,
            'dedicated',
            '{}',
            '{}',
            '{"description": "Root platform tenant for system administration"}',
            true
        )
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_tenants_is_active', table_name='tenants', schema='sentinel')
    op.drop_index('idx_tenants_parent_tenant_id', table_name='tenants', schema='sentinel')
    op.drop_index('idx_tenants_code', table_name='tenants', schema='sentinel')
    
    # Drop table
    op.drop_table('tenants', schema='sentinel')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS sentinel.tenant_type")
    op.execute("DROP TYPE IF EXISTS sentinel.isolation_mode")