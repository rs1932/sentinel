#!/usr/bin/env python3
"""
Simple script to create test user using existing database schema
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.database import get_db_context
from src.utils.password import PasswordManager
from sqlalchemy import text
from uuid import uuid4

def create_simple_test_user():
    """Create a test user using raw SQL to match existing schema"""
    
    print("🏗️  Creating simple test user for API testing")
    print("=" * 50)
    
    password_manager = PasswordManager()
    hashed_password = password_manager.hash_password("password123")
    
    with get_db_context() as db:
        # First, check if TEST tenant exists
        tenant_check = db.execute(
            text("SELECT id FROM sentinel.tenants WHERE code = 'TEST'")
        )
        tenant_row = tenant_check.fetchone()
        
        if not tenant_row:
            # Create TEST tenant using raw SQL
            tenant_id = uuid4()
            db.execute(text("""
                INSERT INTO sentinel.tenants (
                    id, name, code, type, isolation_mode, is_active, 
                    settings, features, tenant_metadata
                ) VALUES (
                    :tenant_id, 'Test Company', 'TEST', 'root', 'shared', true,
                    '{"max_users": 100}', ARRAY['authentication', 'user_management'], '{}'
                )
            """), {"tenant_id": tenant_id})
            print(f"✅ Created TEST tenant")
        else:
            tenant_id = tenant_row[0]
            print(f"✅ Found existing TEST tenant")
        
        # Check if test user exists
        user_check = db.execute(
            text("SELECT id FROM sentinel.users WHERE email = 'test@example.com' AND tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        user_row = user_check.fetchone()
        
        if user_row:
            # Update existing user password
            db.execute(text("""
                UPDATE sentinel.users 
                SET password_hash = :password_hash
                WHERE email = 'test@example.com' AND tenant_id = :tenant_id
            """), {
                "password_hash": hashed_password,
                "tenant_id": tenant_id
            })
            print("✅ Updated existing test user password")
        else:
            # Create new test user
            user_id = uuid4()
            db.execute(text("""
                INSERT INTO sentinel.users (
                    id, tenant_id, email, username, password_hash, 
                    is_service_account, is_active, failed_login_count
                ) VALUES (
                    :user_id, :tenant_id, 'test@example.com', 'testuser', :password_hash,
                    false, true, 0
                )
            """), {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "password_hash": hashed_password
            })
            print("✅ Created new test user")
        
        # Create service account if it doesn't exist
        service_check = db.execute(
            text("SELECT id FROM sentinel.users WHERE email = 'service@example.com' AND tenant_id = :tenant_id"),
            {"tenant_id": tenant_id}
        )
        service_row = service_check.fetchone()
        
        if not service_row:
            service_id = uuid4()
            db.execute(text("""
                INSERT INTO sentinel.users (
                    id, tenant_id, email, username, password_hash,
                    is_service_account, service_account_key, is_active, failed_login_count
                ) VALUES (
                    :service_id, :tenant_id, 'service@example.com', 'service-account', NULL,
                    true, 'test-service-key-123', true, 0
                )
            """), {
                "service_id": service_id,
                "tenant_id": tenant_id
            })
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
    create_simple_test_user()