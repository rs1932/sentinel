"""Add field_definitions table for Module 8

Revision ID: 72cd861f3c60
Revises: c85556e31b52
Create Date: 2025-08-09 00:21:57.795213

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '72cd861f3c60'
down_revision = 'c85556e31b52'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create field_definitions table using direct SQL to avoid enum issues
    op.execute("""
        CREATE TABLE sentinel.field_definitions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            tenant_id UUID REFERENCES sentinel.tenants(id) ON DELETE CASCADE,
            entity_type VARCHAR(100) NOT NULL,
            field_name VARCHAR(100) NOT NULL,
            field_type VARCHAR(50) NOT NULL,
            data_type VARCHAR(50) NOT NULL,
            storage_column VARCHAR(100),
            storage_path VARCHAR(255),
            display_name VARCHAR(255),
            description TEXT,
            validation_rules JSONB DEFAULT '{}',
            default_visibility sentinel.field_permission DEFAULT 'read',
            is_indexed BOOLEAN DEFAULT false,
            is_required BOOLEAN DEFAULT false,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT check_field_type_storage CHECK (
                (field_type = 'core' AND storage_column IS NOT NULL) OR
                (field_type IN ('platform_dynamic', 'tenant_specific') AND storage_path IS NOT NULL)
            )
        )
    """)
    
    # Create unique index with COALESCE for nullable tenant_id to handle uniqueness
    op.execute("""
        CREATE UNIQUE INDEX unique_field_definition 
        ON sentinel.field_definitions(COALESCE(tenant_id, '00000000-0000-0000-0000-000000000000'::uuid), entity_type, field_name)
    """)
    
    # Create indexes
    op.execute("CREATE INDEX idx_field_defs_tenant ON sentinel.field_definitions(tenant_id) WHERE tenant_id IS NOT NULL")
    op.execute("CREATE INDEX idx_field_defs_entity ON sentinel.field_definitions(entity_type)")
    op.execute("CREATE INDEX idx_field_defs_type ON sentinel.field_definitions(field_type)")


def downgrade() -> None:
    # Drop table (will cascade drop indexes and constraints)
    op.execute('DROP TABLE sentinel.field_definitions')