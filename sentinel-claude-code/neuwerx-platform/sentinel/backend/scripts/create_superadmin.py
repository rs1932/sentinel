#!/usr/bin/env python3
"""
Create superadmin user with admin123 password
"""

import asyncio
import json
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
from src.utils.password import password_manager

async def create_platform_tenant_and_admin():
    """Create platform tenant and admin user."""
    print("🚀 Creating platform tenant and superadmin...")
    
    async with AsyncSession(engine) as session:
        try:
            # Create platform tenant
            platform_tenant_id = "00000000-0000-0000-0000-000000000000"
            
            # Check if platform tenant exists
            tenant_result = await session.execute(
                text("SELECT id FROM sentinel.tenants WHERE id = :tenant_id"),
                {"tenant_id": platform_tenant_id}
            )
            
            if not tenant_result.fetchone():
                await session.execute(
                    text("""
                        INSERT INTO sentinel.tenants (id, name, code, type, isolation_mode, is_active, created_at, updated_at)
                        VALUES (:id, :name, :code, 'root', 'dedicated', true, NOW(), NOW())
                    """),
                    {
                        "id": platform_tenant_id,
                        "name": "Sentinel Platform",
                        "code": "PLATFORM"
                    }
                )
                print("✅ Created PLATFORM tenant")
            else:
                print("✅ PLATFORM tenant already exists")
            
            # Hash password
            password_hash = password_manager.hash_password("admin123")
            
            # Check if admin user exists
            admin_result = await session.execute(
                text("SELECT id FROM sentinel.users WHERE email = :email"),
                {"email": "admin@sentinel.com"}
            )
            
            if not admin_result.fetchone():
                # Create admin user
                await session.execute(
                    text("""
                        INSERT INTO sentinel.users (
                            tenant_id, email, username, password_hash, is_active, 
                            attributes, created_at, updated_at
                        )
                        VALUES (:tenant_id, :email, :username, :password_hash, true, :attributes, NOW(), NOW())
                    """),
                    {
                        "tenant_id": platform_tenant_id,
                        "email": "admin@sentinel.com",
                        "username": "admin",
                        "password_hash": password_hash,
                        "attributes": json.dumps({
                            "first_name": "Platform",
                            "last_name": "Administrator",
                            "display_name": "Platform Administrator",
                            "email_verified": True,
                            "role": "superadmin",
                            "created_by": "system"
                        })
                    }
                )
                print("✅ Created admin@sentinel.com user")
            else:
                # Update existing admin password
                await session.execute(
                    text("UPDATE sentinel.users SET password_hash = :password_hash WHERE email = :email"),
                    {"password_hash": password_hash, "email": "admin@sentinel.com"}
                )
                print("✅ Updated admin@sentinel.com password")
            
            await session.commit()
            
            print("\n" + "="*60)
            print("✅ SUPERADMIN SETUP COMPLETED")
            print("="*60)
            print("\n📋 CREDENTIALS:")
            print("  Email: admin@sentinel.com")
            print("  Password: admin123")
            print("  Tenant: PLATFORM")
            print("\n🔒 This account has full system access.")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await session.rollback()
            raise
    
    await engine.dispose()

async def main():
    """Main entry point."""
    if not os.getenv('DATABASE_URL'):
        print("❌ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    await create_platform_tenant_and_admin()

if __name__ == "__main__":
    asyncio.run(main())