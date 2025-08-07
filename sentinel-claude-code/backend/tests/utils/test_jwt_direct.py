#!/usr/bin/env python3
"""
Direct JWT validation test - bypass service layer
"""
import asyncio
import httpx
from src.utils.jwt import jwt_manager

async def test_jwt_direct():
    """Test JWT validation directly"""
    
    print("🔐 Testing JWT Direct Validation...")
    
    # 1. Get a token via login
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "password123", 
                "tenant_code": "TEST"
            }
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            return False
            
        token_data = login_response.json()
        access_token = token_data["access_token"]
        print(f"✅ Token received: {access_token[:20]}...")
        
        # 2. Test direct JWT validation
        try:
            claims = jwt_manager.validate_access_token(access_token)
            print(f"✅ Direct JWT validation successful!")
            print(f"   Claims: {list(claims.keys())}")
            print(f"   User: {claims.get('email', 'N/A')}")
            print(f"   Tenant: {claims.get('tenant_code', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ Direct JWT validation failed: {e}")
            return False

if __name__ == "__main__":
    success = asyncio.run(test_jwt_direct())
    print(f"\n🎯 JWT direct validation: {'✅ PASSED' if success else '❌ FAILED'}")