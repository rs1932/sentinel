#!/usr/bin/env python3
"""
Database Cleanup Script

Preserves only superadmin user and PLATFORM tenant while cleaning all other data
from the sentinel database. This prepares a clean slate for seeding realistic
logistics industry test data.

Maintains referential integrity and resets sequences.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend root to Python path for imports
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import engine
from src.models import *


class DatabaseCleaner:
    """Clean database while preserving superadmin and platform tenant."""
    
    PLATFORM_TENANT_ID = "00000000-0000-0000-0000-000000000000"
    
    def __init__(self):
        self.engine = None
    
    async def initialize(self):
        """Initialize database connection."""
        self.engine = engine
    
    async def backup_superadmin_data(self, session: AsyncSession) -> dict:
        """Backup superadmin and platform tenant data before cleanup."""
        print("🔄 Backing up superadmin and platform tenant data...")
        
        backup_data = {}
        
        # Get platform tenant
        platform_tenant_result = await session.execute(
            text("SELECT * FROM sentinel.tenants WHERE id = :tenant_id"),
            {"tenant_id": self.PLATFORM_TENANT_ID}
        )
        platform_tenant = platform_tenant_result.fetchone()
        if platform_tenant:
            backup_data["platform_tenant"] = dict(platform_tenant._mapping)
            print(f"✅ Backed up platform tenant: {platform_tenant.name}")
        else:
            print("⚠️  Platform tenant not found - will need to recreate")
        
        # Get superadmin users (users on platform tenant)
        superadmin_result = await session.execute(
            text("SELECT * FROM sentinel.users WHERE tenant_id = :tenant_id"),
            {"tenant_id": self.PLATFORM_TENANT_ID}
        )
        superadmins = superadmin_result.fetchall()
        backup_data["superadmins"] = [dict(user._mapping) for user in superadmins]
        print(f"✅ Backed up {len(superadmins)} superadmin user(s)")
        
        # Get superadmin roles and assignments
        if superadmins:
            superadmin_ids = [user.id for user in superadmins]
            
            # Get user roles
            user_roles_result = await session.execute(
                text("SELECT * FROM sentinel.user_roles WHERE user_id = ANY(:user_ids)"),
                {"user_ids": superadmin_ids}
            )
            user_roles = user_roles_result.fetchall()
            backup_data["user_roles"] = [dict(ur._mapping) for ur in user_roles]
            
            # Get roles for superadmins
            if user_roles:
                role_ids = [ur.role_id for ur in user_roles]
                roles_result = await session.execute(
                    text("SELECT * FROM sentinel.roles WHERE id = ANY(:role_ids)"),
                    {"role_ids": role_ids}
                )
                roles = roles_result.fetchall()
                backup_data["roles"] = [dict(role._mapping) for role in roles]
                print(f"✅ Backed up {len(roles)} superadmin role(s)")
        
        return backup_data
    
    async def clean_database_tables(self, session: AsyncSession):
        """Clean all tables except preserved superadmin data."""
        print("🧹 Cleaning database tables...")
        
        # Define cleanup order (respecting foreign key constraints)
        cleanup_tables = [
            # Junction tables first
            "sentinel.user_groups",
            "sentinel.group_roles", 
            "sentinel.role_permissions",
            
            # Dependent entities
            "sentinel.permissions",
            "sentinel.resources",
            "sentinel.groups",
            
            # User-related (preserve superadmin)
            f"sentinel.user_roles WHERE user_id NOT IN (SELECT id FROM sentinel.users WHERE tenant_id = '{self.PLATFORM_TENANT_ID}')",
            f"sentinel.roles WHERE tenant_id != '{self.PLATFORM_TENANT_ID}'",
            f"sentinel.users WHERE tenant_id != '{self.PLATFORM_TENANT_ID}'",
            
            # Note: service_accounts table doesn't exist in current schema
            
            # Token and auth related (clean all - will be regenerated)
            "sentinel.refresh_tokens",
            "sentinel.token_blacklist", 
            "sentinel.password_reset_tokens",
            
            # Tenants (preserve platform)
            f"sentinel.tenants WHERE id != '{self.PLATFORM_TENANT_ID}'"
        ]
        
        for table_condition in cleanup_tables:
            if " WHERE " in table_condition:
                # Conditional delete
                await session.execute(text(f"DELETE FROM {table_condition}"))
            else:
                # Full table truncate
                await session.execute(text(f"TRUNCATE TABLE {table_condition} CASCADE"))
            
            table_name = table_condition.split(" WHERE ")[0] if " WHERE " in table_condition else table_condition
            print(f"  ✅ Cleaned: {table_name}")
        
        await session.commit()
        print("✅ Database cleanup completed")
    
    async def reset_sequences(self, session: AsyncSession):
        """Reset auto-increment sequences for clean IDs."""
        print("🔄 Resetting database sequences...")
        
        # Get all sequences in sentinel schema
        sequences_result = await session.execute(
            text("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = 'sentinel'
            """)
        )
        sequences = sequences_result.fetchall()
        
        for sequence in sequences:
            seq_name = sequence.sequence_name
            await session.execute(text(f"ALTER SEQUENCE sentinel.{seq_name} RESTART WITH 1"))
            print(f"  ✅ Reset sequence: {seq_name}")
        
        await session.commit()
        print("✅ Sequences reset completed")
    
    async def verify_cleanup(self, session: AsyncSession):
        """Verify cleanup was successful and show remaining data."""
        print("🔍 Verifying cleanup results...")
        
        verification_queries = [
            ("tenants", "SELECT COUNT(*) as count, string_agg(name, ', ') as names FROM sentinel.tenants"),
            ("users", "SELECT COUNT(*) as count FROM sentinel.users"),
            ("roles", "SELECT COUNT(*) as count FROM sentinel.roles"), 
            ("groups", "SELECT COUNT(*) as count FROM sentinel.groups"),
            ("permissions", "SELECT COUNT(*) as count FROM sentinel.permissions"),
            ("resources", "SELECT COUNT(*) as count FROM sentinel.resources"),
            # ("service_accounts", "SELECT COUNT(*) as count FROM sentinel.service_accounts")  # Table doesn't exist
        ]
        
        for table_name, query in verification_queries:
            result = await session.execute(text(query))
            row = result.fetchone()
            
            if table_name == "tenants" and hasattr(row, 'names'):
                print(f"  📊 {table_name}: {row.count} remaining ({row.names})")
            else:
                print(f"  📊 {table_name}: {row.count} remaining")
        
        print("✅ Cleanup verification completed")
    
    async def create_platform_tenant_if_missing(self, session: AsyncSession):
        """Create platform tenant if it doesn't exist."""
        # Check if platform tenant exists
        tenant_result = await session.execute(
            text("SELECT id FROM sentinel.tenants WHERE id = :tenant_id"),
            {"tenant_id": self.PLATFORM_TENANT_ID}
        )
        
        if not tenant_result.fetchone():
            print("🔧 Creating missing platform tenant...")
            await session.execute(
                text("""
                    INSERT INTO sentinel.tenants (id, name, code, type, isolation_mode, is_active, created_at, updated_at)
                    VALUES (:id, :name, :code, 'root', 'dedicated', true, NOW(), NOW())
                """),
                {
                    "id": self.PLATFORM_TENANT_ID,
                    "name": "Sentinel Platform",
                    "code": "PLATFORM"
                }
            )
            await session.commit()
            print("✅ Platform tenant created")
    
    async def run_cleanup(self):
        """Run the complete cleanup process."""
        print("🚀 Starting database cleanup process...")
        print(f"Platform Tenant ID: {self.PLATFORM_TENANT_ID}")
        
        await self.initialize()
        
        async with AsyncSession(self.engine) as session:
            try:
                # Backup critical data
                backup_data = await self.backup_superadmin_data(session)
                
                # Ensure platform tenant exists
                await self.create_platform_tenant_if_missing(session)
                
                # Clean database
                await self.clean_database_tables(session)
                
                # Reset sequences for clean slate
                await self.reset_sequences(session)
                
                # Verify results
                await self.verify_cleanup(session)
                
                print("\n✅ Database cleanup completed successfully!")
                print("\nRemaining data:")
                print("- Platform tenant (PLATFORM)")
                print(f"- {len(backup_data.get('superadmins', []))} superadmin user(s)")
                print(f"- {len(backup_data.get('roles', []))} superadmin role(s)")
                print("\nDatabase is ready for logistics industry data seeding.")
                
            except Exception as e:
                print(f"❌ Error during cleanup: {e}")
                await session.rollback()
                raise
            
        await self.engine.dispose()


async def main():
    """Main entry point for database cleanup."""
    print("=" * 60)
    print("🗄️  SENTINEL DATABASE CLEANUP TOOL")
    print("=" * 60)
    
    # Confirm cleanup action
    confirmation = input("\n⚠️  This will DELETE all data except superadmin users and platform tenant.\n"
                        "Are you sure you want to continue? (yes/no): ")
    
    if confirmation.lower() != 'yes':
        print("❌ Cleanup cancelled by user")
        return
    
    cleaner = DatabaseCleaner()
    await cleaner.run_cleanup()


if __name__ == "__main__":
    # Check if database environment is configured
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        print("Please configure database connection before running cleanup")
        sys.exit(1)
    
    asyncio.run(main())