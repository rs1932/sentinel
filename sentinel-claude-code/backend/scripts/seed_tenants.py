#!/usr/bin/env python3
"""
Seed script for Tenant module
Creates sample tenants for testing and development
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.config import settings
from src.database import SessionLocal, init_db
from src.models.tenant import Tenant, TenantType, IsolationMode
from src.services.tenant_service import TenantService
from src.schemas.tenant import TenantCreate, SubTenantCreate

# Sample tenant data
SAMPLE_TENANTS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "Acme Corporation",
        "code": "ACME-001",
        "type": TenantType.ROOT,
        "isolation_mode": IsolationMode.SHARED,
        "settings": {
            "theme": "corporate",
            "timezone": "UTC",
            "language": "en"
        },
        "features": ["multi_factor_auth", "api_access", "sso"],
        "metadata": {
            "industry": "Technology",
            "size": "Enterprise",
            "founded": "2020"
        }
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "name": "Global Shipping Co",
        "code": "GSC-001",
        "type": TenantType.ROOT,
        "isolation_mode": IsolationMode.DEDICATED,
        "settings": {
            "theme": "maritime",
            "timezone": "America/New_York",
            "language": "en"
        },
        "features": ["advanced_audit", "ai_insights", "compliance_reporting"],
        "metadata": {
            "industry": "Logistics",
            "size": "Large",
            "founded": "2015"
        }
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "name": "Healthcare Plus",
        "code": "HCP-001",
        "type": TenantType.ROOT,
        "isolation_mode": IsolationMode.DEDICATED,
        "settings": {
            "theme": "healthcare",
            "timezone": "Europe/London",
            "language": "en"
        },
        "features": ["field_encryption", "compliance_reporting", "advanced_audit"],
        "metadata": {
            "industry": "Healthcare",
            "size": "Medium",
            "founded": "2018"
        }
    }
]

# Sample sub-tenants
SAMPLE_SUB_TENANTS = [
    {
        "parent_code": "ACME-001",
        "name": "Acme East Division",
        "code": "ACME-EAST",
        "isolation_mode": IsolationMode.SHARED,
        "settings": {
            "timezone": "America/New_York",
            "region": "East"
        },
        "features": ["api_access"],
        "metadata": {
            "division": "East",
            "employees": "500"
        }
    },
    {
        "parent_code": "ACME-001",
        "name": "Acme West Division",
        "code": "ACME-WEST",
        "isolation_mode": IsolationMode.SHARED,
        "settings": {
            "timezone": "America/Los_Angeles",
            "region": "West"
        },
        "features": ["api_access"],
        "metadata": {
            "division": "West",
            "employees": "350"
        }
    },
    {
        "parent_code": "GSC-001",
        "name": "GSC European Operations",
        "code": "GSC-EU",
        "isolation_mode": IsolationMode.SHARED,
        "settings": {
            "timezone": "Europe/Amsterdam",
            "region": "Europe"
        },
        "features": ["compliance_reporting"],
        "metadata": {
            "region": "Europe",
            "ports": "15"
        }
    }
]

async def seed_tenants():
    """Create sample tenants"""
    db = SessionLocal()
    service = TenantService(db)
    
    try:
        print("🌱 Seeding tenants...")
        
        # Check if platform tenant exists
        platform_tenant = db.query(Tenant).filter(Tenant.code == "PLATFORM").first()
        if not platform_tenant:
            print("❌ Platform tenant not found. Run migrations first!")
            return
        
        # Create root tenants
        for tenant_data in SAMPLE_TENANTS:
            existing = db.query(Tenant).filter(Tenant.code == tenant_data["code"]).first()
            if existing:
                print(f"⏭️  Tenant {tenant_data['code']} already exists, skipping...")
                continue
            
            tenant = Tenant(
                id=uuid.UUID(tenant_data["id"]),
                name=tenant_data["name"],
                code=tenant_data["code"],
                type=tenant_data["type"],
                isolation_mode=tenant_data["isolation_mode"],
                settings=tenant_data["settings"],
                features=tenant_data["features"],
                metadata=tenant_data["metadata"],  # Will be mapped to tenant_metadata in __init__
                is_active=True
            )
            
            db.add(tenant)
            print(f"✅ Created tenant: {tenant.code} - {tenant.name}")
        
        db.commit()
        
        # Create sub-tenants
        for sub_tenant_data in SAMPLE_SUB_TENANTS:
            parent = db.query(Tenant).filter(Tenant.code == sub_tenant_data["parent_code"]).first()
            if not parent:
                print(f"⚠️  Parent tenant {sub_tenant_data['parent_code']} not found, skipping sub-tenant...")
                continue
            
            existing = db.query(Tenant).filter(Tenant.code == sub_tenant_data["code"]).first()
            if existing:
                print(f"⏭️  Sub-tenant {sub_tenant_data['code']} already exists, skipping...")
                continue
            
            sub_tenant = Tenant(
                id=uuid.uuid4(),
                name=sub_tenant_data["name"],
                code=sub_tenant_data["code"],
                type=TenantType.SUB_TENANT,
                parent_tenant_id=parent.id,
                isolation_mode=sub_tenant_data["isolation_mode"],
                settings=sub_tenant_data["settings"],
                features=sub_tenant_data["features"],
                metadata=sub_tenant_data["metadata"],  # Will be mapped to tenant_metadata in __init__
                is_active=True
            )
            
            db.add(sub_tenant)
            print(f"✅ Created sub-tenant: {sub_tenant.code} under {parent.code}")
        
        db.commit()
        
        # Display summary
        total_tenants = db.query(Tenant).count()
        root_tenants = db.query(Tenant).filter(Tenant.type == TenantType.ROOT).count()
        sub_tenants = db.query(Tenant).filter(Tenant.type == TenantType.SUB_TENANT).count()
        
        print("\n📊 Seeding Summary:")
        print(f"   Total tenants: {total_tenants}")
        print(f"   Root tenants: {root_tenants}")
        print(f"   Sub-tenants: {sub_tenants}")
        
    except Exception as e:
        print(f"❌ Error seeding tenants: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def clear_tenants():
    """Clear all tenants except platform tenant"""
    db = SessionLocal()
    
    try:
        print("🗑️  Clearing non-platform tenants...")
        
        # Delete all non-platform tenants
        deleted = db.query(Tenant).filter(Tenant.code != "PLATFORM").delete()
        db.commit()
        
        print(f"✅ Deleted {deleted} tenants")
        
    except Exception as e:
        print(f"❌ Error clearing tenants: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

async def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tenant seeding script")
    parser.add_argument("--clear", action="store_true", help="Clear all non-platform tenants")
    parser.add_argument("--reseed", action="store_true", help="Clear and reseed tenants")
    
    args = parser.parse_args()
    
    if args.clear:
        await clear_tenants()
    elif args.reseed:
        await clear_tenants()
        await seed_tenants()
    else:
        await seed_tenants()

if __name__ == "__main__":
    asyncio.run(main())