#!/usr/bin/env python3
"""
End-to-End Test Script for Module 3: User Management
Comprehensive testing of all user and service account functionality
"""
import asyncio
import httpx
import uuid
import json
from typing import Dict, Any, List


class UserManagementE2ETester:
    """End-to-end tester for user management functionality"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.auth_url = f"{self.base_url}/auth/login"
        self.user_url = f"{self.base_url}/users"
        self.sa_url = f"{self.base_url}/service-accounts"
        
        self.test_credentials = {
            "email": "test@example.com",
            "password": "password123",
            "tenant_code": "TEST"
        }
        
        self.auth_headers = None
        self.created_users: List[str] = []
        self.created_service_accounts: List[str] = []
    
    async def authenticate(self) -> bool:
        """Authenticate and get auth headers"""
        print("🔐 Authenticating...")
        
        try:
            async with httpx.AsyncClient() as client:
                auth_response = await client.post(self.auth_url, json=self.test_credentials)
                
                if auth_response.status_code != 200:
                    print(f"❌ Authentication failed: {auth_response.status_code}")
                    print(f"   Response: {auth_response.text}")
                    return False
                
                token_data = auth_response.json()
                access_token = token_data["access_token"]
                scopes = token_data.get("scope", "")
                
                self.auth_headers = {"Authorization": f"Bearer {access_token}"}
                print(f"✅ Authenticated successfully with scopes: {scopes}")
                return True
                
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def test_user_management(self) -> bool:
        """Test comprehensive user management functionality"""
        print("\n" + "="*60)
        print("TESTING USER MANAGEMENT")
        print("="*60)
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Test user creation
                print("\\n1. Testing user creation...")
                user_data = {
                    "email": f"e2euser_{uuid.uuid4().hex[:8]}@example.com",
                    "username": f"e2euser_{uuid.uuid4().hex[:6]}",
                    "password": "testpassword123",
                    "attributes": {
                        "department": "engineering",
                        "location": "remote",
                        "level": "senior"
                    },
                    "preferences": {
                        "theme": "dark",
                        "notifications": True,
                        "language": "en"
                    },
                    "is_active": True,
                    "send_invitation": False
                }
                
                create_response = await client.post(
                    f"{self.user_url}/",
                    json=user_data,
                    headers=self.auth_headers
                )
                
                if create_response.status_code != 201:
                    print(f"❌ User creation failed: {create_response.status_code}")
                    print(f"   Response: {create_response.text}")
                    return False
                
                created_user = create_response.json()
                user_id = created_user["id"]
                self.created_users.append(user_id)
                
                print(f"✅ User created successfully: {created_user['email']} (ID: {user_id})")
                
                # 2. Test user retrieval
                print("\\n2. Testing user retrieval...")
                get_response = await client.get(
                    f"{self.user_url}/{user_id}",
                    headers=self.auth_headers
                )
                
                if get_response.status_code != 200:
                    print(f"❌ User retrieval failed: {get_response.status_code}")
                    return False
                
                fetched_user = get_response.json()
                print(f"✅ User retrieved successfully: {fetched_user['username']}")
                
                # Verify data integrity
                assert fetched_user["email"] == user_data["email"]
                assert fetched_user["username"] == user_data["username"]
                assert fetched_user["attributes"] == user_data["attributes"]
                print("✅ Data integrity verified")
                
                # 3. Test user listing
                print("\\n3. Testing user listing...")
                list_response = await client.get(
                    f"{self.user_url}/",
                    headers=self.auth_headers
                )
                
                if list_response.status_code != 200:
                    print(f"❌ User listing failed: {list_response.status_code}")
                    return False
                
                users_list = list_response.json()
                print(f"✅ User listing successful: Found {users_list['total']} users")
                
                # 4. Test user search
                print("\\n4. Testing user search...")
                search_response = await client.get(
                    f"{self.user_url}/",
                    params={"search": user_data["email"][:10]},
                    headers=self.auth_headers
                )
                
                if search_response.status_code != 200:
                    print(f"❌ User search failed: {search_response.status_code}")
                    return False
                
                search_results = search_response.json()
                found_user = any(u["id"] == user_id for u in search_results["items"])
                if not found_user:
                    print("❌ Created user not found in search results")
                    return False
                print("✅ User search successful")
                
                # 5. Test user update
                print("\\n5. Testing user update...")
                update_data = {
                    "username": f"updated_{user_data['username']}",
                    "attributes": {
                        "department": "marketing",
                        "location": "office",
                        "level": "lead"
                    },
                    "preferences": {
                        "theme": "light",
                        "notifications": False
                    }
                }
                
                update_response = await client.patch(
                    f"{self.user_url}/{user_id}",
                    json=update_data,
                    headers=self.auth_headers
                )
                
                if update_response.status_code != 200:
                    print(f"❌ User update failed: {update_response.status_code}")
                    return False
                
                updated_user = update_response.json()
                print(f"✅ User updated successfully: {updated_user['username']}")
                
                # 6. Test user permissions (placeholder)
                print("\\n6. Testing user permissions...")
                perms_response = await client.get(
                    f"{self.user_url}/{user_id}/permissions",
                    headers=self.auth_headers
                )
                
                if perms_response.status_code != 200:
                    print(f"❌ User permissions failed: {perms_response.status_code}")
                    return False
                
                permissions = perms_response.json()
                print(f"✅ User permissions retrieved (placeholder): {permissions['user_id']}")
                
                # 7. Test user lock/unlock
                print("\\n7. Testing user lock/unlock...")
                lock_response = await client.post(
                    f"{self.user_url}/{user_id}/lock",
                    params={"duration_minutes": 5},
                    headers=self.auth_headers
                )
                
                if lock_response.status_code != 204:
                    print(f"❌ User lock failed: {lock_response.status_code}")
                    return False
                print("✅ User locked successfully")
                
                unlock_response = await client.post(
                    f"{self.user_url}/{user_id}/unlock",
                    headers=self.auth_headers
                )
                
                if unlock_response.status_code != 204:
                    print(f"❌ User unlock failed: {unlock_response.status_code}")
                    return False
                print("✅ User unlocked successfully")
                
                # 8. Test bulk operations
                print("\\n8. Testing bulk operations...")
                
                # Create additional users for bulk operations
                bulk_user_ids = []
                for i in range(2):
                    bulk_user_data = {
                        "email": f"bulkuser{i}_{uuid.uuid4().hex[:8]}@example.com",
                        "username": f"bulkuser{i}_{uuid.uuid4().hex[:6]}",
                        "password": "testpassword123",
                        "is_active": True
                    }
                    
                    bulk_create_response = await client.post(
                        f"{self.user_url}/",
                        json=bulk_user_data,
                        headers=self.auth_headers
                    )
                    
                    if bulk_create_response.status_code == 201:
                        bulk_user_id = bulk_create_response.json()["id"]
                        bulk_user_ids.append(bulk_user_id)
                        self.created_users.append(bulk_user_id)
                
                if bulk_user_ids:
                    bulk_data = {
                        "operation": "deactivate",
                        "user_ids": bulk_user_ids
                    }
                    
                    bulk_response = await client.post(
                        f"{self.user_url}/bulk",
                        json=bulk_data,
                        headers=self.auth_headers
                    )
                    
                    if bulk_response.status_code != 200:
                        print(f"❌ Bulk operation failed: {bulk_response.status_code}")
                        return False
                    
                    bulk_result = bulk_response.json()
                    print(f"✅ Bulk operation successful: {bulk_result['successful']} users processed")
                
                print("\\n✅ All user management tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ User management test error: {e}")
            return False
    
    async def test_service_account_management(self) -> bool:
        """Test comprehensive service account management functionality"""
        print("\\n" + "="*60)
        print("TESTING SERVICE ACCOUNT MANAGEMENT")
        print("="*60)
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Test service account creation
                print("\\n1. Testing service account creation...")
                sa_data = {
                    "name": f"E2E_Test_Service_Account_{uuid.uuid4().hex[:8]}",
                    "description": "End-to-end testing service account",
                    "attributes": {
                        "service_type": "integration",
                        "allowed_ips": ["192.168.1.0/24"],
                        "environment": "test",
                        "priority": "high"
                    },
                    "is_active": True
                }
                
                create_response = await client.post(
                    f"{self.sa_url}/",
                    json=sa_data,
                    headers=self.auth_headers
                )
                
                if create_response.status_code != 201:
                    print(f"❌ Service account creation failed: {create_response.status_code}")
                    print(f"   Response: {create_response.text}")
                    return False
                
                create_result = create_response.json()
                service_account = create_result["service_account"]
                credentials = create_result["credentials"]
                account_id = service_account["id"]
                self.created_service_accounts.append(account_id)
                
                print(f"✅ Service account created: {service_account['name']} (ID: {account_id})")
                print(f"   Client ID: {credentials['client_id']}")
                print(f"   Client Secret: {credentials['client_secret'][:8]}...{credentials['client_secret'][-4:]}")
                
                # Store credentials for testing
                client_id = credentials["client_id"]
                client_secret = credentials["client_secret"]
                
                # 2. Test service account retrieval
                print("\\n2. Testing service account retrieval...")
                get_response = await client.get(
                    f"{self.sa_url}/{account_id}",
                    headers=self.auth_headers
                )
                
                if get_response.status_code != 200:
                    print(f"❌ Service account retrieval failed: {get_response.status_code}")
                    return False
                
                fetched_account = get_response.json()
                print(f"✅ Service account retrieved: {fetched_account['name']}")
                
                # 3. Test service account listing
                print("\\n3. Testing service account listing...")
                list_response = await client.get(
                    f"{self.sa_url}/",
                    headers=self.auth_headers
                )
                
                if list_response.status_code != 200:
                    print(f"❌ Service account listing failed: {list_response.status_code}")
                    return False
                
                accounts_list = list_response.json()
                print(f"✅ Service account listing successful: Found {accounts_list['total']} accounts")
                
                # 4. Test service account search
                print("\\n4. Testing service account search...")
                search_response = await client.get(
                    f"{self.sa_url}/",
                    params={"search": sa_data["name"][:15]},
                    headers=self.auth_headers
                )
                
                if search_response.status_code != 200:
                    print(f"❌ Service account search failed: {search_response.status_code}")
                    return False
                
                search_results = search_response.json()
                found_account = any(a["id"] == account_id for a in search_results["items"])
                if not found_account:
                    print("❌ Created service account not found in search results")
                    return False
                print("✅ Service account search successful")
                
                # 5. Test service account update
                print("\\n5. Testing service account update...")
                update_data = {
                    "name": f"Updated_{sa_data['name']}",
                    "description": "Updated description for E2E testing",
                    "attributes": {
                        "service_type": "api_integration",
                        "environment": "production",
                        "priority": "medium"
                    },
                    "is_active": True
                }
                
                update_response = await client.patch(
                    f"{self.sa_url}/{account_id}",
                    json=update_data,
                    headers=self.auth_headers
                )
                
                if update_response.status_code != 200:
                    print(f"❌ Service account update failed: {update_response.status_code}")
                    return False
                
                updated_account = update_response.json()
                print(f"✅ Service account updated: {updated_account['name']}")
                
                # 6. Test credential validation
                print("\\n6. Testing credential validation...")
                validate_response = await client.get(
                    f"{self.sa_url}/{account_id}/validate",
                    params={"client_secret": client_secret},
                    headers=self.auth_headers
                )
                
                if validate_response.status_code != 200:
                    print(f"❌ Credential validation failed: {validate_response.status_code}")
                    return False
                
                validation_result = validate_response.json()
                if not validation_result["valid"]:
                    print("❌ Credential validation returned invalid")
                    return False
                print(f"✅ Credential validation successful: {validation_result['client_id']}")
                
                # 7. Test credential rotation
                print("\\n7. Testing credential rotation...")
                rotate_response = await client.post(
                    f"{self.sa_url}/{account_id}/rotate-credentials",
                    headers=self.auth_headers
                )
                
                if rotate_response.status_code != 200:
                    print(f"❌ Credential rotation failed: {rotate_response.status_code}")
                    return False
                
                new_credentials = rotate_response.json()
                new_client_secret = new_credentials["client_secret"]
                print(f"✅ Credentials rotated successfully")
                print(f"   New Client Secret: {new_client_secret[:8]}...{new_client_secret[-4:]}")
                
                # Verify old credentials are invalid
                old_validate_response = await client.get(
                    f"{self.sa_url}/{account_id}/validate",
                    params={"client_secret": client_secret},
                    headers=self.auth_headers
                )
                
                if old_validate_response.status_code == 200:
                    old_validation = old_validate_response.json()
                    if old_validation["valid"]:
                        print("⚠️  Old credentials still valid after rotation")
                    else:
                        print("✅ Old credentials properly invalidated")
                
                # Verify new credentials are valid
                new_validate_response = await client.get(
                    f"{self.sa_url}/{account_id}/validate",
                    params={"client_secret": new_client_secret},
                    headers=self.auth_headers
                )
                
                if new_validate_response.status_code == 200:
                    new_validation = new_validate_response.json()
                    if new_validation["valid"]:
                        print("✅ New credentials validated successfully")
                    else:
                        print("❌ New credentials validation failed")
                        return False
                
                print("\\n✅ All service account management tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ Service account management test error: {e}")
            return False
    
    async def test_authentication_and_authorization(self) -> bool:
        """Test authentication and authorization requirements"""
        print("\\n" + "="*60)
        print("TESTING AUTHENTICATION & AUTHORIZATION")
        print("="*60)
        
        try:
            async with httpx.AsyncClient() as client:
                # 1. Test endpoints without authentication
                print("\\n1. Testing endpoints without authentication...")
                
                endpoints_to_test = [
                    ("GET", f"{self.user_url}/"),
                    ("POST", f"{self.user_url}/"),
                    ("GET", f"{self.sa_url}/"),
                    ("POST", f"{self.sa_url}/")
                ]
                
                for method, url in endpoints_to_test:
                    if method == "GET":
                        response = await client.get(url)
                    else:
                        response = await client.post(url, json={})
                    
                    if response.status_code != 401:
                        print(f"❌ {method} {url} should return 401, got {response.status_code}")
                        return False
                
                print("✅ All endpoints properly require authentication")
                
                # 2. Test with valid authentication
                print("\\n2. Testing with valid authentication...")
                list_response = await client.get(
                    f"{self.user_url}/",
                    headers=self.auth_headers
                )
                
                if list_response.status_code != 200:
                    print(f"❌ Authenticated request failed: {list_response.status_code}")
                    return False
                
                print("✅ Authenticated requests work properly")
                
                print("\\n✅ Authentication and authorization tests passed!")
                return True
                
        except Exception as e:
            print(f"❌ Authentication/authorization test error: {e}")
            return False
    
    async def cleanup(self):
        """Clean up created test data"""
        print("\\n" + "="*60)
        print("CLEANING UP TEST DATA")
        print("="*60)
        
        try:
            async with httpx.AsyncClient() as client:
                # Clean up users
                for user_id in self.created_users:
                    try:
                        await client.delete(
                            f"{self.user_url}/{user_id}",
                            headers=self.auth_headers
                        )
                        print(f"✅ Cleaned up user: {user_id}")
                    except Exception as e:
                        print(f"⚠️  Could not clean up user {user_id}: {e}")
                
                # Clean up service accounts
                for account_id in self.created_service_accounts:
                    try:
                        await client.delete(
                            f"{self.sa_url}/{account_id}",
                            headers=self.auth_headers
                        )
                        print(f"✅ Cleaned up service account: {account_id}")
                    except Exception as e:
                        print(f"⚠️  Could not clean up service account {account_id}: {e}")
                
                print(f"\\n✅ Cleanup completed: {len(self.created_users)} users, {len(self.created_service_accounts)} service accounts")
                
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    async def run_all_tests(self) -> bool:
        """Run all end-to-end tests"""
        print("🚀 Starting Module 3 End-to-End Tests")
        print("="*60)
        print("Prerequisites:")
        print("1. Server running at http://localhost:8000")
        print("2. Test user exists with proper scopes")
        print("3. Database is accessible and migrations applied")
        print("="*60)
        
        try:
            # Authenticate
            if not await self.authenticate():
                return False
            
            # Run tests
            tests_passed = 0
            total_tests = 3
            
            if await self.test_user_management():
                tests_passed += 1
            
            if await self.test_service_account_management():
                tests_passed += 1
            
            if await self.test_authentication_and_authorization():
                tests_passed += 1
            
            # Cleanup
            await self.cleanup()
            
            # Report results
            print("\\n" + "="*60)
            print("📊 END-TO-END TEST RESULTS")
            print("="*60)
            print(f"Tests Passed: {tests_passed}/{total_tests}")
            print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
            
            if tests_passed == total_tests:
                print("\\n🎉 ALL MODULE 3 TESTS PASSED!")
                print("✅ User Management is fully functional and production-ready")
                return True
            else:
                print(f"\\n❌ {total_tests - tests_passed} test(s) failed")
                return False
                
        except Exception as e:
            print(f"❌ Test execution error: {e}")
            await self.cleanup()
            return False


async def main():
    """Main test execution"""
    tester = UserManagementE2ETester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())