#!/usr/bin/env python3
"""
Super Admin Creation Script for Sentinel Platform

This script creates a super admin user on the PLATFORM tenant with enhanced global permissions.
Super admins have access across all tenants and can perform system-level administration tasks.

Usage:
    python create-super-admin.py --email <email> --password <password> [--tenant-code <code>]

Requirements:
    - Run from the backend directory
    - Virtual environment must be activated (./venv/bin/python)
    - Database must be running and accessible
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the backend src directory to Python path
backend_dir = Path(__file__).parent.parent.parent
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, and_
import uuid
from datetime import datetime

from src.models.user import User
from src.models.tenant import Tenant
from src.utils.password import password_manager
from src.core.config import get_settings


async def create_super_admin(email: str, password: str, tenant_code: str = "PLATFORM"):
    """
    Create a super admin user on the specified tenant (defaults to PLATFORM).
    
    Args:
        email: Email address for the super admin
        password: Password for the super admin
        tenant_code: Tenant code (defaults to PLATFORM for super admin)
    """
    # Get database configuration
    settings = get_settings()
    
    # Create async engine and session
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        future=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Find or create the tenant
            tenant_result = await session.execute(
                select(Tenant).where(Tenant.code == tenant_code.upper())
            )
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                if tenant_code.upper() == "PLATFORM":
                    # Create PLATFORM tenant if it doesn't exist
                    tenant = Tenant(
                        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                        name="Platform Administration",
                        code="PLATFORM",
                        description="System-level platform administration tenant",
                        is_active=True,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(tenant)
                    await session.flush()
                    print(f"✓ Created PLATFORM tenant")
                else:
                    print(f"✗ Error: Tenant '{tenant_code}' does not exist")
                    return False
            else:
                print(f"✓ Found tenant: {tenant.name} ({tenant.code})")
            
            # Check if user already exists
            existing_user = await session.execute(
                select(User).where(
                    and_(
                        User.email == email.lower(),
                        User.tenant_id == tenant.id
                    )
                )
            )
            
            if existing_user.scalar_one_or_none():
                print(f"✗ Error: User '{email}' already exists on tenant '{tenant_code}'")
                return False
            
            # Hash the password
            password_hash = password_manager.hash_password(password)
            
            # Create super admin user
            super_admin = User(
                id=uuid.uuid4(),
                email=email.lower(),
                password_hash=password_hash,
                first_name="Super",
                last_name="Admin",
                tenant_id=tenant.id,
                is_active=True,
                is_service_account=False,
                email_verified=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            session.add(super_admin)
            await session.commit()
            
            print(f"\n🎉 Super Admin Created Successfully!")
            print(f"   Email: {email}")
            print(f"   Tenant: {tenant_code}")
            print(f"   User ID: {super_admin.id}")
            
            if tenant_code.upper() == "PLATFORM":
                print(f"\n🔐 Enhanced Permissions:")
                print(f"   ✓ Global platform administration (platform:admin)")
                print(f"   ✓ Cross-tenant access (tenant:global)")
                print(f"   ✓ Global user management (user:global)")
                print(f"   ✓ Global service account management (service_account:global)")
                print(f"   ✓ Global role management (role:global)")
                print(f"   ✓ System administration (system:admin)")
                print(f"   ✓ Audit log access (audit:read, audit:write)")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error creating super admin: {str(e)}")
            return False
        
        finally:
            await engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description="Create a super admin user for Sentinel Platform"
    )
    parser.add_argument(
        "--email", 
        required=True, 
        help="Email address for the super admin"
    )
    parser.add_argument(
        "--password", 
        required=True, 
        help="Password for the super admin"
    )
    parser.add_argument(
        "--tenant-code", 
        default="PLATFORM",
        help="Tenant code (defaults to PLATFORM for super admin privileges)"
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Creating Super Admin User...")
    print(f"   Email: {args.email}")
    print(f"   Tenant: {args.tenant_code}")
    print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   {'='*50}")
    
    # Run the async function
    success = asyncio.run(create_super_admin(
        email=args.email,
        password=args.password,
        tenant_code=args.tenant_code
    ))
    
    if success:
        print(f"\n✅ Super admin creation completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Super admin creation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()