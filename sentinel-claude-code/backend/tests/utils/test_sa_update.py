#!/usr/bin/env python3
"""
Test service account update specifically
"""
import asyncio
import httpx
import uuid

async def test_sa_update():
    print("Testing service account update...")
    
    async with httpx.AsyncClient() as client:
        # Login
        auth_response = await client.post(
            "http://localhost:8000/api/v1/auth/login",
            json={"email": "test@example.com", "password": "password123", "tenant_code": "TEST"}
        )
        
        if auth_response.status_code != 200:
            print(f"Login failed: {auth_response.status_code}")
            return
            
        token = auth_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create service account
        sa_data = {
            "name": f"Test_SA_{uuid.uuid4().hex[:8]}",
            "description": "Test service account",
            "is_active": True
        }
        
        create_response = await client.post(
            "http://localhost:8000/api/v1/service-accounts/",
            json=sa_data,
            headers=headers
        )
        
        if create_response.status_code != 201:
            print(f"Create failed: {create_response.status_code}")
            print(create_response.text)
            return
            
        sa_id = create_response.json()["service_account"]["id"]
        print(f"Created service account: {sa_id}")
        
        # Update service account
        update_data = {
            "name": f"Updated_Test_SA_{uuid.uuid4().hex[:8]}",
            "description": "Updated test service account"
        }
        
        update_response = await client.patch(
            f"http://localhost:8000/api/v1/service-accounts/{sa_id}",
            json=update_data,
            headers=headers
        )
        
        print(f"Update response: {update_response.status_code}")
        if update_response.status_code != 200:
            print(update_response.text)
        else:
            print("✅ Service account update successful")
            
        # Clean up
        await client.delete(
            f"http://localhost:8000/api/v1/service-accounts/{sa_id}",
            headers=headers
        )

if __name__ == "__main__":
    asyncio.run(test_sa_update())