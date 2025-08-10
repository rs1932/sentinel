#!/usr/bin/env python3
"""
Simple token validation test
"""
import asyncio
import httpx

async def test_token_flow():
    """Test login → token validation → protected endpoint"""
    
    base_url = "http://localhost:8000/api/v1"
    
    print("🔐 Testing Token Flow...")
    
    async with httpx.AsyncClient() as client:
        # 1. Login and get token
        print("\n1. Login...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123", 
                "tenant_code": "TEST"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"✅ Login successful - token received")
        
        # 2. Validate token using auth/validate endpoint
        print("\n2. Validate token...")
        validate_response = await client.get(
            f"{base_url}/auth/validate",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Validate response status: {validate_response.status_code}")
        print(f"Validate response: {validate_response.text}")
        
        # 3. Try protected endpoint (tenant list)
        print("\n3. Test protected endpoint...")
        tenants_response = await client.get(
            f"{base_url}/tenants/",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        print(f"Tenants response status: {tenants_response.status_code}")
        if tenants_response.status_code == 200:
            tenants_data = tenants_response.json()
            print(f"✅ Protected endpoint access successful: {tenants_data.get('total', 0)} tenants")
            return True
        else:
            print(f"❌ Protected endpoint failed: {tenants_response.text}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_token_flow())
    print(f"\n🎯 Token validation test: {'✅ PASSED' if success else '❌ FAILED'}")