#!/usr/bin/env python3
"""
Test script for Tenant CRUD operations
"""
import asyncio
import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1/tenants"

async def test_crud_operations():
    async with httpx.AsyncClient() as client:
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
        
        print("1. Creating tenant...")
        create_response = await client.post(f"{BASE_URL}/", json=create_data)
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
        
        update_response = await client.patch(f"{BASE_URL}/{tenant_id}", json=update_data)
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
        get_response = await client.get(f"{BASE_URL}/{tenant_id}")
        if get_response.status_code == 200:
            fetched_tenant = get_response.json()
            print(f"✅ Fetched tenant: {fetched_tenant['name']}")
            print(f"   Metadata: {fetched_tenant.get('metadata')}")
        else:
            print(f"❌ Failed to get tenant: {get_response.status_code}")
        
        # 4. Delete the tenant
        print("\n4. Deleting tenant...")
        delete_response = await client.delete(f"{BASE_URL}/{tenant_id}")
        if delete_response.status_code == 204:
            print(f"✅ Deleted tenant successfully")
        else:
            print(f"❌ Failed to delete tenant: {delete_response.status_code}")
            print(f"   Response: {delete_response.text}")
        
        # 5. Verify deletion
        print("\n5. Verifying deletion...")
        verify_response = await client.get(f"{BASE_URL}/{tenant_id}")
        if verify_response.status_code == 404:
            print(f"✅ Tenant not found (as expected)")
        else:
            print(f"❌ Tenant still exists: {verify_response.status_code}")

if __name__ == "__main__":
    print("="*60)
    print("TENANT CRUD OPERATIONS TEST")
    print("="*60)
    print("\nMake sure the server is running:")
    print("  uvicorn src.main:app --reload")
    print("\n" + "="*60 + "\n")
    
    try:
        asyncio.run(test_crud_operations())
    except httpx.ConnectError:
        print("❌ Cannot connect to API. Make sure the server is running.")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)