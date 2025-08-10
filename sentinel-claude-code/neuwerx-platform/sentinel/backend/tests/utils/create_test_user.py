#!/usr/bin/env python3
"""
Script to create a test user for API testing
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.database import get_db_context, init_db
from src.models.tenant import Tenant  
from src.models.user import User
from src.utils.password import PasswordManager
from sqlalchemy import select
from uuid import uuid4

def create_test_user():
    """Create a test user for API testing"""
    
    print("🏗️  Creating test user for API testing")
    print("=" * 50)
    
    # Initialize database first
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database init warning: {e}")
    
    password_manager = PasswordManager()
    
    with get_db_context() as db:
        # Check if test tenant exists
        tenant_result = db.execute(
            select(Tenant).where(Tenant.code == "TEST")
        )
        tenant = tenant_result.scalars().first()
        
        if not tenant:
            # Create test tenant
            tenant = Tenant(
                id=uuid4(),
                name="Test Company",
                code="TEST",
                type="root",
                isolation_mode="shared",
                is_active=True,
                settings={
                    "max_users": 100,
                    "features": ["authentication", "basic_access"]
                },
                features=["authentication", "user_management"]
            )
            db.add(tenant)
            db.flush()
            print(f"✅ Created test tenant: {tenant.code}")
        else:
            print(f"✅ Found existing tenant: {tenant.code}")
        
        # Check if test user exists
        user_result = db.execute(
            select(User).where(
                User.email == "test@example.com",
                User.tenant_id == tenant.id
            )
        )
        existing_user = user_result.scalars().first()
        
        if existing_user:
            print("⚠️  Test user already exists, updating password...")
            # Update password
            existing_user.password_hash = password_manager.hash_password("password123")
            test_user = existing_user
        else:
            # Create test user
            test_user = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email="test@example.com",
                username="testuser",
                password_hash=password_manager.hash_password("password123"),
                is_service_account=False,
                failed_login_attempts="0",
                is_active=True,
                email_verified=True
            )
            db.add(test_user)
            print("✅ Created new test user")
        
        # Also create a service account for testing
        service_result = db.execute(
            select(User).where(
                User.email == "service@example.com",
                User.tenant_id == tenant.id
            )
        )
        service_user = service_result.scalars().first()
        
        if not service_user:
            service_account = User(
                id=uuid4(),
                tenant_id=tenant.id,
                email="service@example.com",
                username="service-account",
                password_hash=None,  # Service accounts use API keys
                is_service_account=True,
                service_account_key="test-service-key-123",
                failed_login_attempts="0",
                is_active=True,
                email_verified=True
            )
            db.add(service_account)
            print("✅ Created service account")
        
        db.commit()
    
    print("\n🎯 Test Credentials Created:")
    print("-" * 30)
    print("Regular User Login:")
    print(f"  Email: test@example.com")
    print(f"  Password: password123")
    print(f"  Tenant Code: TEST")
    print()
    print("Service Account:")
    print(f"  Client ID: service@example.com") 
    print(f"  Client Secret: test-service-key-123")
    print(f"  Tenant Code: TEST")
    print()
    print("🚀 You can now test the login API:")
    print("POST /api/v1/auth/login")
    print('{"email": "test@example.com", "password": "password123", "tenant_code": "TEST"}')

if __name__ == "__main__":
    create_test_user()