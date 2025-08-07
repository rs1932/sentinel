#!/usr/bin/env python3
"""
Debug login response
"""
import asyncio
import httpx

async def debug_login():
    """Debug login to see response structure"""
    
    base_url = "http://localhost:8000/api/v1"
    test_credentials = {
        "email": "test@example.com",
        "password": "NewSecurePassword4$7!",
        "tenant_code": "TEST"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/auth/login",
            json=test_credentials
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_login())