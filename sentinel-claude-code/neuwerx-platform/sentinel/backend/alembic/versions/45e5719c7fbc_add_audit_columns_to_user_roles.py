"""add_audit_columns_to_user_roles

Revision ID: 45e5719c7fbc
Revises: 5d08be7e2a62
Create Date: 2025-08-07 11:14:00.570020

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '45e5719c7fbc'
down_revision = '5d08be7e2a62'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_at and updated_at columns to user_roles table
    op.add_column('user_roles', 
        sa.Column('created_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False),
        schema='sentinel'
    )
    
    op.add_column('user_roles', 
        sa.Column('updated_at', sa.DateTime(timezone=True), 
                  server_default=sa.text('now()'), nullable=False),
        schema='sentinel'
    )
    
    # Create an update trigger for updated_at column
    op.execute("""
        CREATE OR REPLACE FUNCTION sentinel.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_user_roles_updated_at 
        BEFORE UPDATE ON sentinel.user_roles 
        FOR EACH ROW 
        EXECUTE FUNCTION sentinel.update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop the trigger first
    op.execute("DROP TRIGGER IF EXISTS update_user_roles_updated_at ON sentinel.user_roles")
    
    # Drop the columns
    op.drop_column('user_roles', 'updated_at', schema='sentinel')
    op.drop_column('user_roles', 'created_at', schema='sentinel')