#!/usr/bin/env python3
"""
Update test user password to policy-compliant password
"""
from sqlalchemy import create_engine, text
from src.config import settings
from src.utils.password import password_manager

def update_test_user_password():
    """Update test user password"""
    
    print("🔐 Updating Test User Password")
    print("-" * 40)
    
    # Create sync engine for this operation
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.connect() as db:
            # Hash the new password
            new_password = "NewSecurePassword4$7!"
            hashed_password = password_manager.hash_password(new_password)
            
            # Update the test user's password
            result = db.execute(text("""
                UPDATE sentinel.users 
                SET password_hash = :password_hash
                WHERE email = 'test@example.com'
            """), {"password_hash": hashed_password})
            
            db.commit()
            
            if result.rowcount > 0:
                print(f"✅ Test user password updated successfully!")
                print(f"📧 Email: test@example.com")
                print(f"🔑 New Password: {new_password}")
                print(f"🏢 Tenant Code: TEST")
            else:
                print("⚠️  Test user not found")
    
    except Exception as e:
        print(f"❌ Failed to update password: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    update_test_user_password()