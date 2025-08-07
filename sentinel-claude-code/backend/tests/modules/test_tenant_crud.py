#!/usr/bin/env python3
"""
Test script for Tenant CRUD operations with JWT authentication
"""
import asyncio
import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1/tenants"
AUTH_URL = "http://localhost:8000/api/v1/auth/login"

# Test credentials - adjust these based on your test setup
TEST_CREDENTIALS = {
    "email": "test@example.com",
    "password": "password123", 
    "tenant_code": "TEST"
}

async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Get authentication token for API requests"""
    print("🔐 Authenticating...")
    
    auth_response = await client.post(AUTH_URL, json=TEST_CREDENTIALS)
    if auth_response.status_code != 200:
        raise Exception(f"Authentication failed: {auth_response.status_code} - {auth_response.text}")
    
    token_data = auth_response.json()
    access_token = token_data["access_token"]
    scopes = token_data.get("scope", "")
    
    print(f"✅ Authenticated successfully with scopes: {scopes}")
    return access_token

def get_auth_headers(token: str) -> dict:
    """Get authorization headers for API requests"""
    return {"Authorization": f"Bearer {token}"}

async def test_crud_operations():
    async with httpx.AsyncClient() as client:
        try:
            # Get authentication token
            token = await get_auth_token(client)
            headers = get_auth_headers(token)
            
            # 1. Create a test tenant
            test_code = f"TEST-{uuid4().hex[:8].upper()}"
            create_data = {
                "name": "Test Tenant for CRUD",
                "code": test_code,
                "type": "root",
                "isolation_mode": "shared",
                "settings": {"theme": "light"},
                "features": ["api_access"],
                "metadata": {"test": "initial"}
            }
            
            print("\n1. Creating tenant...")
            create_response = await client.post(f"{BASE_URL}/", json=create_data, headers=headers)
            if create_response.status_code != 201:
                print(f"❌ Failed to create tenant: {create_response.status_code}")
                print(f"   Response: {create_response.text}")
                return
        
            tenant = create_response.json()
            tenant_id = tenant["id"]
            print(f"✅ Created tenant: {tenant['name']} (ID: {tenant_id})")
            print(f"   Metadata: {tenant.get('metadata')}")
            
            # 2. Update the tenant
            print("\n2. Updating tenant...")
            update_data = {
                "name": "Updated Test Tenant",
                "metadata": {"test": "updated", "version": 2},
                "settings": {"theme": "dark", "locale": "en-US"}
            }
            
            update_response = await client.patch(f"{BASE_URL}/{tenant_id}", json=update_data, headers=headers)
            if update_response.status_code == 200:
                updated_tenant = update_response.json()
                print(f"✅ Updated tenant: {updated_tenant['name']}")
                print(f"   New metadata: {updated_tenant.get('metadata')}")
                print(f"   New settings: {updated_tenant.get('settings')}")
            else:
                print(f"❌ Failed to update tenant: {update_response.status_code}")
                print(f"   Response: {update_response.text}")
            
            # 3. Get the tenant to verify update
            print("\n3. Getting tenant details...")
            get_response = await client.get(f"{BASE_URL}/{tenant_id}", headers=headers)
            if get_response.status_code == 200:
                fetched_tenant = get_response.json()
                print(f"✅ Fetched tenant: {fetched_tenant['name']}")
                print(f"   Metadata: {fetched_tenant.get('metadata')}")
            else:
                print(f"❌ Failed to get tenant: {get_response.status_code}")
            
            # 4. Delete the tenant
            print("\n4. Deleting tenant...")
            delete_response = await client.delete(f"{BASE_URL}/{tenant_id}", headers=headers)
            if delete_response.status_code == 204:
                print(f"✅ Deleted tenant successfully")
            else:
                print(f"❌ Failed to delete tenant: {delete_response.status_code}")
                print(f"   Response: {delete_response.text}")
            
            # 5. Verify deletion
            print("\n5. Verifying deletion...")
            verify_response = await client.get(f"{BASE_URL}/{tenant_id}", headers=headers)
            if verify_response.status_code == 404:
                print(f"✅ Tenant not found (as expected)")
            else:
                print(f"❌ Tenant still exists: {verify_response.status_code}")
                
        except Exception as e:
            print(f"❌ Authentication or connection error: {e}")
            return

if __name__ == "__main__":
    print("="*60)
    print("TENANT CRUD OPERATIONS TEST (WITH JWT AUTHENTICATION)")
    print("="*60)
    print("\nPrerequisites:")
    print("1. Server is running: uvicorn src.main:app --reload")
    print("2. Test user exists with tenant:admin scopes")
    print("3. Database is initialized")
    print(f"\nUsing credentials: {TEST_CREDENTIALS['email']}")
    print("\n" + "="*60 + "\n")
    
    try:
        asyncio.run(test_crud_operations())
    except httpx.ConnectError:
        print("❌ Cannot connect to API. Make sure the server is running.")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)