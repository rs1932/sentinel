#!/usr/bin/env python3
"""
Simple Logistics Industry Seed Data Script
Creates 3 tenant companies with 4 users each for RBAC testing
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

async def seed_logistics_data():
    """Create 3 logistics tenants with 4 users each."""
    print("🌱 Starting simple logistics data seeding...")
    
    # Tenant data
    tenant_data = [
        {
            "name": "Maritime Port Operations",
            "code": "MARITIME",
            "domain": "maritime.logistics.com",
            "industry": "Maritime Logistics",
            "headquarters": "Singapore"
        },
        {
            "name": "AirCargo Express", 
            "code": "AIRCARGO",
            "domain": "aircargo.express.com",
            "industry": "Air Cargo",
            "headquarters": "Frankfurt"
        },
        {
            "name": "GroundLink Logistics",
            "code": "GROUNDLINK", 
            "domain": "groundlink.logistics.com",
            "industry": "Ground Logistics",
            "headquarters": "Memphis"
        }
    ]
    
    # User data for each tenant
    user_templates = {
        "MARITIME": [
            {"email": "port.manager@maritime.com", "name": "Sarah Thompson", "role": "Manager"},
            {"email": "vessel.coord@maritime.com", "name": "Marcus Chen", "role": "Coordinator"},
            {"email": "customs.officer@maritime.com", "name": "Ahmed Hassan", "role": "Officer"},
            {"email": "dock.worker@maritime.com", "name": "Jose Rodriguez", "role": "Worker"}
        ],
        "AIRCARGO": [
            {"email": "ops.manager@aircargo.com", "name": "Lisa Wagner", "role": "Manager"},
            {"email": "flight.coord@aircargo.com", "name": "David Kim", "role": "Coordinator"},
            {"email": "security.inspector@aircargo.com", "name": "Emma Johnson", "role": "Inspector"},
            {"email": "cargo.handler@aircargo.com", "name": "Carlos Mendez", "role": "Handler"}
        ],
        "GROUNDLINK": [
            {"email": "warehouse.mgr@groundlink.com", "name": "Michael O'Connor", "role": "Manager"},
            {"email": "logistics.coord@groundlink.com", "name": "Priya Patel", "role": "Coordinator"},
            {"email": "compliance.officer@groundlink.com", "name": "Jennifer Lee", "role": "Officer"},
            {"email": "warehouse.associate@groundlink.com", "name": "Robert Johnson", "role": "Associate"}
        ]
    }
    
    password = "LogisticsTest2024!"
    hashed_password = password_manager.hash_password(password)
    
    async with AsyncSession(engine) as session:
        try:
            created_tenants = {}
            
            # Get existing tenants or create if missing
            print("🏢 Processing logistics company tenants...")
            for data in tenant_data:
                # Check if tenant exists
                result = await session.execute(
                    text("SELECT id FROM sentinel.tenants WHERE code = :code"),
                    {"code": data["code"]}
                )
                tenant_id = result.scalar()
                
                if tenant_id:
                    created_tenants[data["code"]] = tenant_id
                    print(f"  ✅ Found existing tenant: {data['name']} ({data['code']})")
                else:
                    # Create new tenant
                    await session.execute(
                        text("""
                            INSERT INTO sentinel.tenants (
                                name, code, type, isolation_mode, is_active, 
                                tenant_metadata, created_at, updated_at
                            )
                            VALUES (:name, :code, 'root', 'shared', true, :metadata, NOW(), NOW())
                        """),
                        {
                            "name": data["name"],
                            "code": data["code"],
                            "metadata": json.dumps({
                                "domain": data["domain"],
                                "industry": data["industry"],
                                "headquarters": data["headquarters"],
                                "currency": "USD",
                                "timezone": "UTC"
                            })
                        }
                    )
                    
                    # Get the created tenant ID
                    result = await session.execute(
                        text("SELECT id FROM sentinel.tenants WHERE code = :code"),
                        {"code": data["code"]}
                    )
                    tenant_id = result.scalar()
                    created_tenants[data["code"]] = tenant_id
                    
                    print(f"  ✅ Created tenant: {data['name']} ({data['code']})")
            
            await session.commit()
            
            # Create users (skip if already exists)
            print("👨‍💼 Creating test users...")
            for tenant_code, tenant_id in created_tenants.items():
                users_data = user_templates[tenant_code]
                
                for user_data in users_data:
                    # Check if user exists
                    existing_user = await session.execute(
                        text("SELECT email FROM sentinel.users WHERE email = :email"),
                        {"email": user_data["email"]}
                    )
                    
                    if existing_user.scalar():
                        print(f"    ✅ User already exists: {user_data['name']} ({user_data['email']})")
                    else:
                        await session.execute(
                            text("""
                                INSERT INTO sentinel.users (
                                    tenant_id, email, username, password_hash, is_active,
                                    attributes, created_at, updated_at
                                )
                                VALUES (:tenant_id, :email, :username, :password_hash, true, :attributes, NOW(), NOW())
                            """),
                            {
                                "tenant_id": tenant_id,
                                "email": user_data["email"],
                                "username": user_data["email"].split("@")[0],
                                "password_hash": hashed_password,
                                "attributes": json.dumps({
                                    "first_name": user_data["name"].split()[0],
                                    "last_name": user_data["name"].split()[-1],
                                    "display_name": user_data["name"],
                                    "email_verified": True,
                                    "role": user_data["role"],
                                    "test_account": True,
                                    "default_password": password
                                })
                            }
                        )
                        print(f"    ✅ Created user: {user_data['name']} ({user_data['email']}) - {user_data['role']}")
            
            await session.commit()
            
            # Generate summary
            print("\n" + "="*60)
            print("📊 LOGISTICS INDUSTRY SEED DATA SUMMARY")
            print("="*60)
            
            # Count entities
            tenant_count = await session.execute(text("SELECT COUNT(*) FROM sentinel.tenants"))
            user_count = await session.execute(text("SELECT COUNT(*) FROM sentinel.users"))
            
            print(f"\n📈 Entity Counts:")
            print(f"  Tenants: {tenant_count.scalar()}")
            print(f"  Users: {user_count.scalar()}")
            
            print(f"\n🏢 Tenants Created:")
            for data in tenant_data:
                print(f"  {data['name']} ({data['code']}) - {data['industry']}")
            
            print(f"\n👥 User Credentials (Password: {password}):")
            print(f"  SUPERADMIN: admin@sentinel.com / admin123 (PLATFORM)")
            for tenant_code, users_data in user_templates.items():
                print(f"  {tenant_code}:")
                for user_data in users_data:
                    print(f"    {user_data['email']} - {user_data['name']}")
            
            print(f"\n✅ Database seeding completed successfully!")
            print("Ready for RBAC testing with realistic logistics scenarios.")
            
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
    
    await seed_logistics_data()

if __name__ == "__main__":
    asyncio.run(main())