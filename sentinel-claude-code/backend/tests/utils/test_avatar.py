#!/usr/bin/env python3
"""
Test avatar functionality
"""
import asyncio
import httpx
import io
from PIL import Image

async def create_test_image(size=(256, 256), format='PNG'):
    """Create a test image in memory"""
    # Create a simple colored image
    image = Image.new('RGB', size, color='red')
    
    # Add some pattern to make it more realistic
    from PIL import ImageDraw
    draw = ImageDraw.Draw(image)
    draw.rectangle([size[0]//4, size[1]//4, 3*size[0]//4, 3*size[1]//4], fill='blue')
    draw.ellipse([size[0]//3, size[1]//3, 2*size[0]//3, 2*size[1]//3], fill='green')
    
    # Save to bytes
    image_bytes = io.BytesIO()
    image.save(image_bytes, format=format)
    image_bytes.seek(0)
    
    return image_bytes.getvalue()

async def test_avatar_upload():
    """Test avatar upload functionality"""
    
    print("🖼️ Testing Avatar Upload Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    test_credentials = {
        "email": "test@example.com",
        "password": "NewSecurePassword4$7!",
        "tenant_code": "TEST"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Step 1: Login to get token
        print("\n1. Logging in...")
        login_response = await client.post(
            f"{base_url}/auth/login",
            json=test_credentials
        )
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.text}")
            return False
        
        login_data = login_response.json()
        token = login_data["access_token"]
        user_id = login_data["user_id"]
        
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   ✅ Login successful, user_id: {user_id}")
        
        # Step 2: Create test image
        print("\n2. Creating test image...")
        test_image_data = await create_test_image()
        print(f"   ✅ Created test image ({len(test_image_data)} bytes)")
        
        # Step 3: Upload avatar
        print("\n3. Uploading avatar...")
        files = {
            "file": ("test_avatar.png", test_image_data, "image/png")
        }
        
        upload_response = await client.post(
            f"{base_url}/users/{user_id}/avatar",
            headers=headers,
            files=files
        )
        
        print(f"   Status: {upload_response.status_code}")
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            print(f"   ✅ Avatar uploaded successfully!")
            print(f"   📂 File ID: {upload_data['file_id']}")
            print(f"   🔗 Default URL: {upload_data['default_url']}")
            print(f"   📐 Available sizes: {upload_data['sizes']}")
            
            # Step 4: Get avatar info
            print("\n4. Getting avatar info...")
            info_response = await client.get(
                f"{base_url}/users/{user_id}/avatar",
                headers=headers,
                params={"size": "medium"}
            )
            
            print(f"   Status: {info_response.status_code}")
            if info_response.status_code == 200:
                info_data = info_response.json()
                print(f"   ✅ Avatar info retrieved!")
                print(f"   🔗 URL: {info_data['url']}")
                print(f"   📐 Size: {info_data['size']}")
                
                # Step 5: Get all avatar URLs
                print("\n5. Getting all avatar URLs...")
                urls_response = await client.get(
                    f"{base_url}/users/{user_id}/avatar/urls",
                    headers=headers
                )
                
                print(f"   Status: {urls_response.status_code}")
                if urls_response.status_code == 200:
                    urls_data = urls_response.json()
                    print(f"   ✅ All URLs retrieved!")
                    for size, url in urls_data.items():
                        print(f"   📐 {size}: {url}")
                    
                    # Step 6: Test serving avatar file
                    print("\n6. Testing avatar file serving...")
                    avatar_url = urls_data['medium'].replace(base_url, "")
                    serve_response = await client.get(f"{base_url}{avatar_url}")
                    
                    print(f"   Status: {serve_response.status_code}")
                    if serve_response.status_code == 200:
                        content_type = serve_response.headers.get('content-type')
                        content_length = len(serve_response.content)
                        print(f"   ✅ Avatar served successfully!")
                        print(f"   📄 Content-Type: {content_type}")
                        print(f"   📏 Content-Length: {content_length} bytes")
                        
                        # Step 7: Delete avatar
                        print("\n7. Testing avatar deletion...")
                        delete_response = await client.delete(
                            f"{base_url}/users/{user_id}/avatar",
                            headers=headers
                        )
                        
                        print(f"   Status: {delete_response.status_code}")
                        if delete_response.status_code == 200:
                            print(f"   ✅ Avatar deleted successfully!")
                            
                            # Step 8: Verify deletion
                            print("\n8. Verifying avatar deletion...")
                            verify_response = await client.get(
                                f"{base_url}/users/{user_id}/avatar",
                                headers=headers
                            )
                            
                            print(f"   Status: {verify_response.status_code}")
                            if verify_response.status_code == 404:
                                print(f"   ✅ Avatar properly deleted!")
                                return True
                            else:
                                print(f"   ❌ Avatar still exists: {verify_response.text}")
                        else:
                            print(f"   ❌ Avatar deletion failed: {delete_response.text}")
                    else:
                        print(f"   ❌ Avatar serving failed: {serve_response.text}")
                else:
                    print(f"   ❌ URLs retrieval failed: {urls_response.text}")
            else:
                print(f"   ❌ Avatar info failed: {info_response.text}")
        else:
            print(f"   ❌ Avatar upload failed: {upload_response.text}")
    
    return False

async def test_avatar_validation():
    """Test avatar validation and error cases"""
    
    print("\n🔒 Testing Avatar Validation")
    print("=" * 50)
    
    base_url = "http://localhost:8000/api/v1"
    test_credentials = {
        "email": "test@example.com",
        "password": "NewSecurePassword4$7!",
        "tenant_code": "TEST"
    }
    
    async with httpx.AsyncClient() as client:
        
        # Login
        login_response = await client.post(
            f"{base_url}/auth/login",
            json=test_credentials
        )
        
        if login_response.status_code != 200:
            print(f"❌ Login failed for validation tests")
            return False
        
        login_data = login_response.json()
        token = login_data["access_token"]
        user_id = login_data["user_id"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 1: Invalid file format
        print("\n1. Testing invalid file format...")
        invalid_file = b"This is not an image"
        files = {
            "file": ("test.txt", invalid_file, "text/plain")
        }
        
        response = await client.post(
            f"{base_url}/users/{user_id}/avatar",
            headers=headers,
            files=files
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print(f"   ✅ Invalid format properly rejected")
        else:
            print(f"   ⚠️  Expected 400, got {response.status_code}")
        
        # Test 2: Permission check (try to upload for another user)
        print("\n2. Testing permission check...")
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        test_image_data = await create_test_image()
        files = {
            "file": ("test_avatar.png", test_image_data, "image/png")
        }
        
        response = await client.post(
            f"{base_url}/users/{fake_user_id}/avatar",
            headers=headers,
            files=files
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 403:
            print(f"   ✅ Permission check working correctly")
        else:
            print(f"   ⚠️  Expected 403, got {response.status_code}")
        
        # Test 3: Invalid size parameter
        print("\n3. Testing invalid size parameter...")
        response = await client.get(
            f"{base_url}/users/{user_id}/avatar",
            headers=headers,
            params={"size": "invalid_size"}
        )
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 400:
            print(f"   ✅ Invalid size properly rejected")
        else:
            print(f"   ⚠️  Expected 400, got {response.status_code}")
        
        return True

async def main():
    """Run all avatar tests"""
    
    print("🧪 Avatar Testing Suite")
    print("=" * 60)
    print("Prerequisites:")
    print("1. Server running at http://localhost:8000")
    print("2. Test user exists with updated password")
    print("=" * 60)
    
    tests = [
        ("Avatar Upload Workflow", test_avatar_upload),
        ("Avatar Validation", test_avatar_validation),
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