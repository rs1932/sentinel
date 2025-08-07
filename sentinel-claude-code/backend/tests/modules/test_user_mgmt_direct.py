#!/usr/bin/env python3
"""
Direct User Management Test - bypass service validation layer
"""
import asyncio
import httpx
import uuid

async def test_user_mgmt_direct():
    """Test user management endpoints directly with working JWT"""
    
    print("👥 Testing User Management Direct...")
    
    # 1. Get a working token
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
        headers = {"Authorization": f"Bearer {access_token}"}
        print(f"✅ Token obtained for testing")
        
        # 2. Test user creation 
        print("\n2. Testing user creation...")
        user_data = {
            "email": f"testuser_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"testuser_{uuid.uuid4().hex[:6]}",
            "password": "testpassword123",
            "is_active": True
        }
        
        create_response = await client.post(
            "http://localhost:8000/api/v1/users/",
            json=user_data,
            headers=headers
        )
        
        print(f"Create response status: {create_response.status_code}")
        
        if create_response.status_code == 201:
            user = create_response.json()
            user_id = user["id"]
            print(f"✅ User created successfully: {user['email']}")
            
            # 3. Test user list
            print("\n3. Testing user list...")
            list_response = await client.get(
                "http://localhost:8000/api/v1/users/",
                headers=headers
            )
            
            print(f"List response status: {list_response.status_code}")
            if list_response.status_code == 200:
                users_list = list_response.json()
                print(f"✅ User list retrieved: {users_list.get('total', 0)} users")
                
                # 4. Test user get
                print("\n4. Testing user get...")
                get_response = await client.get(
                    f"http://localhost:8000/api/v1/users/{user_id}",
                    headers=headers
                )
                
                print(f"Get response status: {get_response.status_code}")
                if get_response.status_code == 200:
                    fetched_user = get_response.json()
                    print(f"✅ User retrieved: {fetched_user['email']}")
                    
                    # 5. Cleanup - delete user
                    print("\n5. Testing user deletion...")
                    delete_response = await client.delete(
                        f"http://localhost:8000/api/v1/users/{user_id}",
                        headers=headers
                    )
                    
                    print(f"Delete response status: {delete_response.status_code}")
                    if delete_response.status_code == 204:
                        print("✅ User deleted successfully")
                        return True
                    else:
                        print(f"❌ Delete failed: {delete_response.text}")
                else:
                    print(f"❌ Get failed: {get_response.text}")
            else:
                print(f"❌ List failed: {list_response.text}")
        else:
            print(f"❌ Create failed: {create_response.text}")
            if create_response.status_code == 401:
                print("Token validation issue detected")
            
        return False

if __name__ == "__main__":
    success = asyncio.run(test_user_mgmt_direct())
    print(f"\n🎯 User management direct test: {'✅ PASSED' if success else '❌ FAILED'}")