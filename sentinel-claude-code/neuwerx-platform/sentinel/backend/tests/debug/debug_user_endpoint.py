#!/usr/bin/env python3
"""
Debug user management endpoint
"""
import asyncio
import httpx

async def debug_user_endpoint():
    """Debug user endpoint issues"""
    
    base_url = "http://localhost:8000/api/v1"
    test_credentials = {
        "email": "test@example.com",
        "password": "NewSecurePassword4$7!",
        "tenant_code": "TEST"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("1. Testing login...")
        response = await client.post(f"{base_url}/auth/login", json=test_credentials)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            login_data = response.json()
            token = login_data["access_token"]
            user_id = login_data["user_id"]
            headers = {"Authorization": f"Bearer {token}"}
            
            print(f"✅ Login successful, user_id: {user_id}")
            
            # 2. Test /users/me endpoint
            print("\n2. Testing /users/me endpoint...")
            me_response = await client.get(f"{base_url}/users/me", headers=headers)
            print(f"Status: {me_response.status_code}")
            print(f"Response: {me_response.text}")
            
            # 3. Test tenant endpoint
            print("\n3. Testing /tenants endpoint...")
            tenant_response = await client.get(f"{base_url}/tenants/", headers=headers)
            print(f"Status: {tenant_response.status_code}")
            print(f"Response: {tenant_response.text[:500]}...")
            
        else:
            print(f"❌ Login failed: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_user_endpoint())