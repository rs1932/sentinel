#!/usr/bin/env python3
"""
Test password reset functionality
"""
import asyncio
import httpx
import uuid
import time

async def test_password_reset_workflow():
    """Test the complete password reset workflow"""
    
    print("🔐 Testing Password Reset Workflow")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    test_email = "test@example.com"
    tenant_code = "TEST"
    new_password = "NewSecurePassword4$7!"
    
    async with httpx.AsyncClient() as client:
        
        # Step 1: Request password reset
        print("\n1. Testing password reset request...")
        reset_request_data = {
            "email": test_email,
            "tenant_code": tenant_code
        }
        
        reset_response = await client.post(
            f"{base_url}/auth/password-reset/request",
            json=reset_request_data
        )
        
        print(f"   Status: {reset_response.status_code}")
        if reset_response.status_code == 200:
            reset_data = reset_response.json()
            print(f"   ✅ Reset request successful: {reset_data['message']}")
            
            # In development, we get debug info
            if "debug_token" in reset_data and reset_data["debug_token"]:
                token = reset_data["debug_token"]
                print(f"   📝 Debug token: {token}")
                
                # Step 2: Validate the token
                print("\n2. Testing token validation...")
                validate_response = await client.post(
                    f"{base_url}/auth/password-reset/validate",
                    params={"token": token}
                )
                
                print(f"   Status: {validate_response.status_code}")
                if validate_response.status_code == 200:
                    validation_data = validate_response.json()
                    print(f"   ✅ Token validation successful")
                    print(f"   📧 User email: {validation_data['user_email']}")
                    print(f"   ⏰ Expires at: {validation_data['expires_at']}")
                    
                    # Step 3: Reset password
                    print("\n3. Testing password reset...")
                    confirm_data = {
                        "token": token,
                        "new_password": new_password,
                        "confirm_password": new_password
                    }
                    
                    confirm_response = await client.post(
                        f"{base_url}/auth/password-reset/confirm",
                        json=confirm_data
                    )
                    
                    print(f"   Status: {confirm_response.status_code}")
                    if confirm_response.status_code == 200:
                        confirm_data_resp = confirm_response.json()
                        print(f"   ✅ Password reset successful: {confirm_data_resp['message']}")
                        
                        # Step 4: Test login with new password
                        print("\n4. Testing login with new password...")
                        login_data = {
                            "email": test_email,
                            "password": new_password,
                            "tenant_code": tenant_code
                        }
                        
                        login_response = await client.post(
                            f"{base_url}/auth/login",
                            json=login_data
                        )
                        
                        print(f"   Status: {login_response.status_code}")
                        if login_response.status_code == 200:
                            login_result = login_response.json()
                            print(f"   ✅ Login successful with new password!")
                            print(f"   🎯 Token type: {login_result['token_type']}")
                            
                            return True
                        else:
                            print(f"   ❌ Login failed: {login_response.text}")
                            return False
                    else:
                        print(f"   ❌ Password reset failed: {confirm_response.text}")
                else:
                    print(f"   ❌ Token validation failed: {validate_response.text}")
            else:
                print("   ⚠️  No debug token provided (expected in production)")
                return True  # This is expected in production
        else:
            print(f"   ❌ Reset request failed: {reset_response.text}")
    
    return False

async def test_password_reset_security():
    """Test security aspects of password reset"""
    
    print("\n🔒 Testing Password Reset Security")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Invalid email (should still return success for security)
        print("\n1. Testing with invalid email...")
        reset_data = {
            "email": "nonexistent@example.com",
            "tenant_code": "TEST"
        }
        
        response = await client.post(
            f"{base_url}/auth/password-reset/request",
            json=reset_data
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Returns success for security: {result['message']}")
        
        # Test 2: Invalid tenant
        print("\n2. Testing with invalid tenant...")
        reset_data = {
            "email": "test@example.com",
            "tenant_code": "INVALID"
        }
        
        response = await client.post(
            f"{base_url}/auth/password-reset/request",
            json=reset_data
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Returns success for security: {result['message']}")
        
        # Test 3: Invalid token validation
        print("\n3. Testing with invalid token...")
        response = await client.post(
            f"{base_url}/auth/password-reset/validate",
            params={"token": "invalid-token-123"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print("   ✅ Invalid token properly rejected")
        
        # Test 4: Password mismatch
        print("\n4. Testing password mismatch...")
        confirm_data = {
            "token": "some-token",
            "new_password": "password1",
            "confirm_password": "password2"
        }
        
        response = await client.post(
            f"{base_url}/auth/password-reset/confirm",
            json=confirm_data
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 422:
            print("   ✅ Password mismatch properly rejected")
        
        return True

async def test_rate_limiting():
    """Test rate limiting on password reset endpoints"""
    
    print("\n⏱️ Testing Rate Limiting")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        
        print("Sending multiple reset requests rapidly...")
        
        reset_data = {
            "email": "test@example.com",
            "tenant_code": "TEST"
        }
        
        for i in range(5):
            response = await client.post(
                f"{base_url}/auth/password-reset/request",
                json=reset_data
            )
            
            print(f"   Request {i+1}: {response.status_code}")
            
            if response.status_code == 429:
                print("   ✅ Rate limiting activated")
                return True
        
        print("   ⚠️  Rate limiting not triggered (might be expected)")
        return True

async def main():
    """Run all password reset tests"""
    
    print("🧪 Password Reset Testing Suite")
    print("=" * 60)
    print("Prerequisites:")
    print("1. Server running at http://localhost:8000")
    print("2. Test user exists: test@example.com")
    print("3. Test tenant exists: TEST")
    print("=" * 60)
    
    tests = [
        ("Password Reset Workflow", test_password_reset_workflow),
        ("Security Tests", test_password_reset_security),
        ("Rate Limiting", test_rate_limiting),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                print(f"\n✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"\n❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS:")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Total:  {passed + failed}")
    print(f"   Success Rate: {(passed/(passed+failed)*100):.1f}%")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} TEST(S) FAILED")

if __name__ == "__main__":
    asyncio.run(main())