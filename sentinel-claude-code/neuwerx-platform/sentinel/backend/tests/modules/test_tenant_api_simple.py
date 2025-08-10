#!/usr/bin/env python3
"""
Simple tenant API test that works with running server
"""
import requests
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"
TENANT_URL = f"{BASE_URL}/tenants"
AUTH_URL = f"{BASE_URL}/auth/login"

# Test credentials
TEST_CREDENTIALS = {
    "email": "test@example.com",
    "password": "password123", 
    "tenant_code": "TEST"
}

def get_auth_headers():
    """Get authentication headers"""
    print("🔐 Authenticating...")
    
    response = requests.post(AUTH_URL, json=TEST_CREDENTIALS)
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
        
    token_data = response.json()
    access_token = token_data["access_token"]
    scopes = token_data.get("scope", "")
    
    print(f"✅ Authenticated successfully with scopes: {scopes}")
    return {"Authorization": f"Bearer {access_token}"}

def test_create_tenant():
    """Test creating a tenant"""
    headers = get_auth_headers()
    if not headers:
        return False
        
    tenant_data = {
        "name": "Test Company",
        "code": f"TEST-{uuid4().hex[:8].upper()}",
        "type": "root",
        "isolation_mode": "shared",
        "settings": {"theme": "light"},
        "features": ["api_access", "sso"],
        "metadata": {"industry": "technology"}
    }
    
    print("\n1. Testing CREATE tenant...")
    response = requests.post(f"{TENANT_URL}/", json=tenant_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ CREATE successful: {data['name']} (ID: {data['id']})")
        return data["id"]
    else:
        print(f"❌ CREATE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_get_tenant(tenant_id):
    """Test getting a tenant"""
    headers = get_auth_headers()
    if not headers:
        return False
        
    print(f"\n2. Testing GET tenant {tenant_id}...")
    response = requests.get(f"{TENANT_URL}/{tenant_id}", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ GET successful: {data['name']}")
        return True
    else:
        print(f"❌ GET failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_list_tenants():
    """Test listing tenants"""
    headers = get_auth_headers()
    if not headers:
        return False
        
    print("\n3. Testing LIST tenants...")
    response = requests.get(f"{TENANT_URL}/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ LIST successful: Found {data['total']} tenants")
        return True
    else:
        print(f"❌ LIST failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_update_tenant(tenant_id):
    """Test updating a tenant"""
    headers = get_auth_headers()
    if not headers:
        return False
        
    update_data = {
        "name": "Updated Test Company",
        "settings": {"theme": "dark"},
        "features": ["multi_factor_auth", "api_access"]
    }
    
    print(f"\n4. Testing UPDATE tenant {tenant_id}...")
    response = requests.patch(f"{TENANT_URL}/{tenant_id}", json=update_data, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ UPDATE successful: {data['name']}")
        return True
    else:
        print(f"❌ UPDATE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_delete_tenant(tenant_id):
    """Test deleting a tenant"""
    headers = get_auth_headers()
    if not headers:
        return False
        
    print(f"\n5. Testing DELETE tenant {tenant_id}...")
    response = requests.delete(f"{TENANT_URL}/{tenant_id}", headers=headers)
    
    if response.status_code == 204:
        print(f"✅ DELETE successful")
        return True
    else:
        print(f"❌ DELETE failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_authentication_failure():
    """Test that endpoints require authentication"""
    print("\n6. Testing authentication requirement...")
    
    # Try without auth headers
    response = requests.get(f"{TENANT_URL}/")
    
    if response.status_code == 401:
        print("✅ Authentication requirement working (401 without token)")
        return True
    else:
        print(f"❌ Authentication requirement failed: {response.status_code}")
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("TENANT API INTEGRATION TESTS")
    print("="*60)
    print("\nPrerequisites:")
    print("1. Server running at http://localhost:8000")
    print("2. Test user exists with proper scopes")
    print("\n" + "="*60)
    
    try:
        # Test authentication failure first
        if not test_authentication_failure():
            print("\n❌ Authentication tests failed")
            return
            
        # Test list operation
        if not test_list_tenants():
            print("\n❌ List tests failed")
            return
            
        # Test create operation
        tenant_id = test_create_tenant()
        if not tenant_id:
            print("\n❌ Create tests failed")
            return
            
        # Test get operation
        if not test_get_tenant(tenant_id):
            print("\n❌ Get tests failed")
            return
            
        # Test update operation
        if not test_update_tenant(tenant_id):
            print("\n❌ Update tests failed")
            return
            
        # Test delete operation
        if not test_delete_tenant(tenant_id):
            print("\n❌ Delete tests failed")
            return
            
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running at http://localhost:8000")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    main()