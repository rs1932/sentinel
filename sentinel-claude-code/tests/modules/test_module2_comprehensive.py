#!/usr/bin/env python3
"""
Comprehensive Module 2 (Tenant Management) Test Suite

Tests all tenant management functionality including:
- Tenant CRUD operations
- Tenant hierarchy management
- Tenant activation/deactivation
- API endpoints with authentication
- Error handling and edge cases
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any, List
from uuid import uuid4


class TenantManagementTestSuite:
    """Comprehensive tenant management functionality tester"""
    
    def __init__(self):
        self.timestamp = int(time.time())
        self.base_url = "http://localhost:8000/api/v1"
        self.test_credentials = {
            "email": "test@example.com",
            "password": "password123",
            "tenant_code": "TEST"
        }
        self.access_token = None
        self.user_id = None
        self.tenant_id = None
        self.client = None
        self.test_results = []
        
        # Test data
        self.created_tenants = []
        
    async def setup(self):
        """Initialize test client and authenticate"""
        self.client = httpx.AsyncClient(timeout=60.0, follow_redirects=True)
        
        # Login to get access token
        login_response = await self.client.post(
            f"{self.base_url}/auth/login",
            json=self.test_credentials
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            self.access_token = login_data["access_token"]
            self.user_id = login_data["user_id"]
            self.tenant_id = login_data.get("tenant_id")
            return True
        else:
            print(f"❌ Authentication failed: {login_response.status_code} - {login_response.text}")
            return False
    
    async def teardown(self):
        """Clean up test data and client"""
        # Clean up created tenants (in reverse order for hierarchy)
        for tenant_id in reversed(self.created_tenants):
            try:
                await self.client.delete(
                    f"{self.base_url}/tenants/{tenant_id}",
                    headers=self.get_headers()
                )
            except:
                pass
        
        if self.client:
            await self.client.aclose()
    
    def get_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.access_token}"}
    
    def record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {test_name}: {status}" + (f" - {details}" if details else ""))

    async def test_tenant_creation(self):
        """Test 1: Tenant Creation and Validation"""
        print("\\n🏢 Test 1: Tenant Creation and Validation")
        print("-" * 60)
        
        # Test 1.1: Create basic tenant
        tenant_data = {
            "name": f"Test Company {self.timestamp}",
            "code": f"COMP{self.timestamp}",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = await self.client.post(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            json=tenant_data
        )
        
        success = create_response.status_code == 201
        self.record_test_result(
            "Create Basic Tenant",
            success,
            f"Status: {create_response.status_code}"
        )
        
        basic_tenant_id = None
        if success:
            tenant_response = create_response.json()
            basic_tenant_id = tenant_response["id"]
            self.created_tenants.append(basic_tenant_id)
            
            # Validate response structure
            required_fields = ["id", "name", "code", "type", "isolation_mode"]
            fields_present = all(field in tenant_response for field in required_fields)
            self.record_test_result(
                "Tenant Response Structure",
                fields_present,
                f"Required fields present: {fields_present}"
            )
        
        # Test 1.2: Create tenant with metadata and settings
        tenant_data_extended = {
            "name": f"Extended Tenant {self.timestamp}",
            "code": f"EXT{self.timestamp}",
            "type": "root",
            "isolation_mode": "dedicated",
            "metadata": {"region": "us-west", "tier": "premium"},
            "settings": {"theme": "dark", "notifications": True}
        }
        
        extended_response = await self.client.post(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            json=tenant_data_extended
        )
        
        success = extended_response.status_code == 201
        self.record_test_result(
            "Create Extended Tenant",
            success,
            f"Status: {extended_response.status_code}"
        )
        
        if success:
            extended_tenant = extended_response.json()
            self.created_tenants.append(extended_tenant["id"])
        
        # Test 1.3: Duplicate tenant code validation
        duplicate_response = await self.client.post(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            json=tenant_data  # Same data as before
        )
        
        self.record_test_result(
            "Duplicate Tenant Code Rejection",
            duplicate_response.status_code == 409,
            f"Status: {duplicate_response.status_code}"
        )
        
        # Test 1.4: Invalid tenant data validation
        invalid_tenant_data = {
            "name": "",  # Empty name should be rejected
            "code": "INVALID",
            "type": "invalid_type"
        }
        
        invalid_response = await self.client.post(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            json=invalid_tenant_data
        )
        
        self.record_test_result(
            "Invalid Tenant Data Rejection",
            invalid_response.status_code == 422,
            f"Status: {invalid_response.status_code}"
        )

    async def test_tenant_retrieval(self):
        """Test 2: Tenant Retrieval and Listing"""
        print("\\n📋 Test 2: Tenant Retrieval and Listing")
        print("-" * 60)
        
        # Test 2.1: List all tenants
        list_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=self.get_headers()
        )
        
        success = list_response.status_code == 200
        self.record_test_result(
            "List All Tenants",
            success,
            f"Status: {list_response.status_code}"
        )
        
        tenants = []
        if success:
            list_data = list_response.json()
            tenants = list_data.get("items", [])
            
            # Validate list structure
            required_fields = ["items", "total", "skip", "limit"]
            fields_present = all(field in list_data for field in required_fields)
            self.record_test_result(
                "Tenant List Structure",
                fields_present,
                f"Found {len(tenants)} tenants"
            )
        
        # Test 2.2: Get specific tenant details
        if tenants and len(tenants) > 0:
            tenant_id = tenants[0]["id"]
            detail_response = await self.client.get(
                f"{self.base_url}/tenants/{tenant_id}",
                headers=self.get_headers()
            )
            
            success = detail_response.status_code == 200
            self.record_test_result(
                "Get Tenant Details",
                success,
                f"Status: {detail_response.status_code}"
            )
        
        # Test 2.3: Tenant filtering by type
        filtered_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            params={"type": "root"}
        )
        
        self.record_test_result(
            "Tenant Filtering by Type",
            filtered_response.status_code == 200,
            f"Status: {filtered_response.status_code}"
        )
        
        # Test 2.4: Tenant search functionality
        search_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            params={"search": "test"}
        )
        
        self.record_test_result(
            "Tenant Search Functionality",
            search_response.status_code == 200,
            f"Status: {search_response.status_code}"
        )
        
        # Test 2.5: Pagination
        paginated_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            params={"skip": 0, "limit": 2}
        )
        
        self.record_test_result(
            "Tenant Pagination",
            paginated_response.status_code == 200,
            f"Status: {paginated_response.status_code}"
        )

    async def test_tenant_updates(self):
        """Test 3: Tenant Updates and Modification"""
        print("\\n📝 Test 3: Tenant Updates and Modification")
        print("-" * 60)
        
        if not self.created_tenants:
            self.record_test_result(
                "Tenant Update Test",
                False,
                "No tenants available for update testing"
            )
            return
        
        # Test 3.1: Update tenant information
        tenant_id = self.created_tenants[0]
        update_data = {
            "name": f"Updated Tenant {self.timestamp}",
            "settings": {"theme": "light", "notifications": False},
            "metadata": {"updated": True, "version": 2}
        }
        
        update_response = await self.client.patch(
            f"{self.base_url}/tenants/{tenant_id}",
            headers=self.get_headers(),
            json=update_data
        )
        
        success = update_response.status_code == 200
        self.record_test_result(
            "Update Tenant Information",
            success,
            f"Status: {update_response.status_code}"
        )
        
        if success:
            updated_tenant = update_response.json()
            name_updated = updated_tenant.get("name") == f"Updated Tenant {self.timestamp}"
            self.record_test_result(
                "Tenant Update Verification",
                name_updated,
                f"Name updated: {name_updated}"
            )
        
        # Test 3.2: Update non-existent tenant
        fake_tenant_id = str(uuid4())
        fake_update_response = await self.client.patch(
            f"{self.base_url}/tenants/{fake_tenant_id}",
            headers=self.get_headers(),
            json={"name": "Should not work"}
        )
        
        self.record_test_result(
            "Non-Existent Tenant Update",
            fake_update_response.status_code == 404,
            f"Status: {fake_update_response.status_code}"
        )

    async def test_tenant_hierarchy(self):
        """Test 4: Tenant Hierarchy Management"""
        print("\\n🌲 Test 4: Tenant Hierarchy Management")
        print("-" * 60)
        
        # Create a parent tenant for hierarchy testing
        parent_tenant_data = {
            "name": f"Parent Tenant {self.timestamp}",
            "code": f"PARENT{self.timestamp}",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        parent_response = await self.client.post(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            json=parent_tenant_data
        )
        
        success = parent_response.status_code == 201
        self.record_test_result(
            "Create Parent Tenant",
            success,
            f"Status: {parent_response.status_code}"
        )
        
        if success:
            parent_tenant = parent_response.json()
            parent_tenant_id = parent_tenant["id"]
            self.created_tenants.append(parent_tenant_id)
            
            # Create sub-tenant
            sub_tenant_data = {
                "name": f"Sub Tenant {self.timestamp}",
                "code": f"SUB{self.timestamp}",
                "type": "sub_tenant",
                "isolation_mode": "shared"
            }
            
            sub_response = await self.client.post(
                f"{self.base_url}/tenants/{parent_tenant_id}/sub-tenants",
                headers=self.get_headers(),
                json=sub_tenant_data
            )
            
            success = sub_response.status_code == 201
            self.record_test_result(
                "Create Sub-Tenant",
                success,
                f"Status: {sub_response.status_code}"
            )
            
            if success:
                sub_tenant = sub_response.json()
                self.created_tenants.append(sub_tenant["id"])
                
                # Verify parent-child relationship
                parent_id_match = sub_tenant.get("parent_tenant_id") == parent_tenant_id
                self.record_test_result(
                    "Sub-Tenant Parent Relationship",
                    parent_id_match,
                    f"Parent ID matches: {parent_id_match}"
                )
                
                # Test hierarchy retrieval
                hierarchy_response = await self.client.get(
                    f"{self.base_url}/tenants/{parent_tenant_id}/hierarchy",
                    headers=self.get_headers()
                )
                
                self.record_test_result(
                    "Get Tenant Hierarchy",
                    hierarchy_response.status_code == 200,
                    f"Status: {hierarchy_response.status_code}"
                )

    async def test_tenant_activation(self):
        """Test 5: Tenant Activation and Deactivation"""
        print("\\n🔄 Test 5: Tenant Activation and Deactivation")
        print("-" * 60)
        
        if not self.created_tenants:
            self.record_test_result(
                "Tenant Activation Test",
                False,
                "No tenants available for activation testing"
            )
            return
        
        tenant_id = self.created_tenants[0]
        
        # Test 5.1: Deactivate tenant
        deactivate_response = await self.client.post(
            f"{self.base_url}/tenants/{tenant_id}/deactivate",
            headers=self.get_headers()
        )
        
        success = deactivate_response.status_code == 200
        self.record_test_result(
            "Deactivate Tenant",
            success,
            f"Status: {deactivate_response.status_code}"
        )
        
        # Test 5.2: Activate tenant
        activate_response = await self.client.post(
            f"{self.base_url}/tenants/{tenant_id}/activate",
            headers=self.get_headers()
        )
        
        self.record_test_result(
            "Activate Tenant",
            activate_response.status_code == 200,
            f"Status: {activate_response.status_code}"
        )

    async def test_authentication_and_authorization(self):
        """Test 6: Authentication and Authorization"""
        print("\\n🔐 Test 6: Authentication and Authorization")
        print("-" * 60)
        
        # Test 6.1: Unauthorized access (no token)
        unauth_response = await self.client.get(f"{self.base_url}/tenants/")
        
        self.record_test_result(
            "Unauthorized Access Rejection",
            unauth_response.status_code == 401,
            f"Status: {unauth_response.status_code}"
        )
        
        # Test 6.2: Invalid token
        invalid_headers = {"Authorization": "Bearer invalid-token-12345"}
        invalid_token_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=invalid_headers
        )
        
        self.record_test_result(
            "Invalid Token Rejection",
            invalid_token_response.status_code == 401,
            f"Status: {invalid_token_response.status_code}"
        )

    async def test_error_handling(self):
        """Test 7: Error Handling and Edge Cases"""
        print("\\n⚠️ Test 7: Error Handling and Edge Cases")
        print("-" * 60)
        
        # Test 7.1: Invalid UUID in URL
        invalid_uuid_response = await self.client.get(
            f"{self.base_url}/tenants/not-a-valid-uuid",
            headers=self.get_headers()
        )
        
        self.record_test_result(
            "Invalid UUID Handling",
            invalid_uuid_response.status_code == 422,
            f"Status: {invalid_uuid_response.status_code}"
        )
        
        # Test 7.2: Large pagination request
        large_limit_response = await self.client.get(
            f"{self.base_url}/tenants/",
            headers=self.get_headers(),
            params={"limit": 1000}  # Exceeds max limit
        )
        
        self.record_test_result(
            "Large Pagination Limit",
            large_limit_response.status_code == 422,
            f"Status: {large_limit_response.status_code}"
        )

    async def run_all_tests(self):
        """Run all tenant management tests"""
        print("🏢 COMPREHENSIVE TENANT MANAGEMENT TEST SUITE")
        print("=" * 80)
        print("Testing all Module 2 functionality:")
        print("• Tenant CRUD operations")
        print("• Tenant hierarchy management")
        print("• Tenant activation/deactivation")
        print("• Authentication and authorization")
        print("• Error handling and edge cases")
        print("=" * 80)
        
        # Setup
        if not await self.setup():
            print("❌ Test setup failed - authentication not working")
            return
        
        # Run all test suites
        test_suites = [
            ("Tenant Creation", self.test_tenant_creation),
            ("Tenant Retrieval", self.test_tenant_retrieval),
            ("Tenant Updates", self.test_tenant_updates),
            ("Tenant Hierarchy", self.test_tenant_hierarchy),
            ("Tenant Activation", self.test_tenant_activation),
            ("Authentication & Authorization", self.test_authentication_and_authorization),
            ("Error Handling & Edge Cases", self.test_error_handling),
        ]
        
        for suite_name, suite_func in test_suites:
            try:
                await suite_func()
            except Exception as e:
                print(f"💥 {suite_name} Suite: ERROR - {e}")
                self.record_test_result(f"{suite_name} Suite", False, f"Exception: {e}")
        
        # Generate comprehensive summary
        await self.generate_test_report()
        
        # Cleanup
        await self.teardown()

    async def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\\n" + "=" * 80)
        print("📊 MODULE 2 TENANT MANAGEMENT TEST REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests Executed: {total_tests}")
        print(f"Tests Passed: {passed_tests}")
        print(f"Tests Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("-" * 80)
        
        # Categorize results
        categories = {
            "Tenant Creation": [],
            "Tenant Retrieval": [],
            "Tenant Updates": [],
            "Tenant Hierarchy": [],
            "Tenant Activation": [],
            "Authentication": [],
            "Error Handling": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            categorized = False
            for category in categories:
                category_keywords = category.lower().split()
                if any(keyword in test_name.lower() for keyword in category_keywords):
                    categories[category].append(result)
                    categorized = True
                    break
            
            if not categorized:
                categories["Error Handling"].append(result)
        
        # Print category summaries
        for category, results in categories.items():
            if results:
                category_passed = sum(1 for r in results if r["passed"])
                category_total = len(results)
                category_rate = (category_passed / category_total) * 100
                
                print(f"\\n{category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
                
                for result in results:
                    status = "✅" if result["passed"] else "❌"
                    details = f" - {result['details']}" if result['details'] else ""
                    print(f"  {status} {result['test']}{details}")
        
        # Failed tests summary
        if failed_tests > 0:
            print(f"\\n⚠️ FAILED TESTS SUMMARY:")
            print("-" * 40)
            for result in self.test_results:
                if not result["passed"]:
                    print(f"❌ {result['test']}")
                    if result['details']:
                        print(f"   Details: {result['details']}")
        
        # Overall assessment
        print("\\n" + "=" * 80)
        if success_rate >= 95:
            print("🎉 EXCELLENT! Module 2 Tenant Management is working perfectly.")
            print("   ✅ All core functionality tested and validated")
            print("   ✅ Ready for production deployment")
        elif success_rate >= 85:
            print("✅ VERY GOOD! Module 2 is mostly working correctly.")
            print("   ✅ Core functionality working")
            print("   ⚠️ Minor issues may need attention")
        elif success_rate >= 70:
            print("⚠️ GOOD! Core tenant management is working.")
            print("   ✅ Basic functionality working")
            print("   ⚠️ Several issues need to be addressed")
        else:
            print("❌ NEEDS ATTENTION! Multiple issues found in tenant management.")
            print("   ❌ Significant problems detected")
            print("   ❌ Fix issues before production deployment")
        
        print("=" * 80)
        return success_rate


async def main():
    """Run the comprehensive tenant management test suite"""
    test_suite = TenantManagementTestSuite()
    success_rate = await test_suite.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success_rate >= 85 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())