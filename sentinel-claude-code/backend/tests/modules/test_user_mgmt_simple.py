#!/usr/bin/env python3
"""
Test Module 3 User Management with simpler auth
"""
import asyncio
import httpx
import uuid

async def test_with_working_tenant_auth():
    """Since tenant endpoints work, let's see if user endpoints work with same token approach"""
    
    print("👥 Testing User Management with Tenant-style Auth...")
    
    # Get token the same way tenant tests do
    async with httpx.AsyncClient() as client:
        # First get the token like the tenant test
        auth_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123",
                "tenant_code": "TEST"
            }
        )
        
        if auth_response.status_code != 200:
            print(f"❌ Auth failed: {auth_response.status_code}")
            return False
            
        token_data = auth_response.json()
        access_token = token_data["access_token"]
        print(f"✅ Token received")
        
        # Test if tenant endpoint still works with this token (control test)
        print("\n1. Control test - tenant list (known working)...")
        tenant_response = await client.get(
            "http://localhost:8000/api/v1/tenants/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Tenant response: {tenant_response.status_code}")
        if tenant_response.status_code == 200:
            print("✅ Tenant endpoint works - token is valid")
        else:
            print(f"❌ Even tenant endpoint failing: {tenant_response.text}")
            return False
        
        # Now test user endpoint 
        print("\n2. Test user list endpoint...")
        user_response = await client.get(
            "http://localhost:8000/api/v1/users/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"User response: {user_response.status_code}")
        if user_response.status_code == 200:
            users_data = user_response.json()
            print(f"✅ User endpoint works! Found {users_data.get('total', 0)} users")
            return True
        else:
            print(f"❌ User endpoint fails: {user_response.text}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_with_working_tenant_auth())
    print(f"\n🎯 User management test result: {'✅ PASSED' if success else '❌ FAILED'}")