#!/usr/bin/env python3
"""
Quick test to verify metadata handling is working correctly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import json
from uuid import uuid4

# Test the model directly
def test_model():
    from src.models.tenant import Tenant
    
    print("Testing Tenant model...")
    
    # Create a tenant with metadata
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        code="TEST-001",
        type="root",
        isolation_mode="shared",
        metadata={"test": "value", "key": 123},  # Using 'metadata' in API
        settings={},
        features=[],
        is_active=True
    )
    
    # Test that metadata is stored correctly
    print(f"tenant.tenant_metadata = {tenant.tenant_metadata}")
    
    # Test to_dict
    tenant_dict = tenant.to_dict()
    print(f"\ntenant.to_dict() = {json.dumps(tenant_dict, indent=2, default=str)}")
    
    # Check that 'metadata' is in the dict, not 'tenant_metadata'
    assert 'metadata' in tenant_dict, "to_dict() should return 'metadata' key"
    assert 'tenant_metadata' not in tenant_dict, "to_dict() should not return 'tenant_metadata' key"
    
    print("\n✅ Model test passed!")

# Test the schema
def test_schema():
    from src.models.tenant import Tenant
    from src.schemas.tenant import TenantResponse
    
    print("\nTesting TenantResponse schema...")
    
    # Create a tenant
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        code="TEST-002",
        type="root",
        isolation_mode="shared",
        metadata={"schema": "test"},
        settings={"theme": "dark"},
        features=["api_access"],
        is_active=True
    )
    
    # Convert to response
    response = TenantResponse.from_orm(tenant)
    
    print(f"TenantResponse = {response.model_dump_json(indent=2)}")
    
    # Check that metadata is properly serialized
    assert response.metadata == {"schema": "test"}, "Schema should have metadata"
    
    print("\n✅ Schema test passed!")

# Test API endpoint
async def test_api():
    import httpx
    
    print("\nTesting API endpoint...")
    
    test_data = {
        "name": "API Test Tenant",
        "code": f"API-TEST-{uuid4().hex[:8].upper()}",
        "type": "root",
        "isolation_mode": "shared",
        "settings": {"api": "test"},
        "features": ["api_access"],
        "metadata": {"created_by": "test_script", "version": 1}
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Try to create a tenant
            response = await client.post(
                "http://localhost:8000/api/v1/tenants/",
                json=test_data
            )
            
            if response.status_code == 201:
                data = response.json()
                print(f"Created tenant: {json.dumps(data, indent=2)}")
                
                # Check metadata in response
                assert 'metadata' in data, "Response should have 'metadata' field"
                assert data['metadata'] == test_data['metadata'], "Metadata should match"
                
                print("\n✅ API test passed!")
                
                # Clean up - delete the test tenant
                tenant_id = data['id']
                delete_response = await client.delete(f"http://localhost:8000/api/v1/tenants/{tenant_id}")
                if delete_response.status_code == 204:
                    print("✅ Test tenant cleaned up")
            else:
                print(f"❌ API returned {response.status_code}: {response.text}")
                
    except httpx.ConnectError:
        print("❌ Cannot connect to API. Make sure the server is running:")
        print("   uvicorn src.main:app --reload")

if __name__ == "__main__":
    print("="*60)
    print("METADATA HANDLING TEST")
    print("="*60)
    
    # Test model
    test_model()
    
    # Test schema
    test_schema()
    
    # Test API (if server is running)
    asyncio.run(test_api())
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print("="*60)