#!/usr/bin/env python3
"""
Complete Regression Test Suite for All Modules
Systematically tests all implemented features across Module 1, 2, and 3
"""
import asyncio
import subprocess
import sys
import time
from pathlib import Path

class RegressionTestSuite:
    def __init__(self):
        self.test_results = []
        self.start_time = None
        
    def record_result(self, test_name: str, passed: bool, details: str = "", duration: float = 0):
        """Record test result"""
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details,
            "duration": duration
        })
        status = "✅ PASSED" if passed else "❌ FAILED"
        duration_str = f" ({duration:.2f}s)" if duration > 0 else ""
        print(f"   {test_name}: {status}{duration_str}")
        if details:
            print(f"      {details}")
    
    async def run_python_test(self, test_file: str, test_name: str, timeout: int = 120):
        """Run a Python test file and capture results"""
        print(f"\n🧪 Running {test_name}...")
        print("-" * 60)
        
        start = time.time()
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=Path.cwd()
            )
            duration = time.time() - start
            
            if result.returncode == 0:
                # Parse output for success indicators
                output = result.stdout.lower()
                if any(keyword in output for keyword in ["all tests passed", "success rate: 100", "passed: "]):
                    self.record_result(test_name, True, "All checks passed", duration)
                    return True
                else:
                    self.record_result(test_name, True, "Completed successfully", duration)
                    return True
            else:
                error_msg = result.stderr.strip() or "Test failed with non-zero exit code"
                self.record_result(test_name, False, f"Error: {error_msg[:100]}...", duration)
                return False
                
        except subprocess.TimeoutExpired:
            self.record_result(test_name, False, f"Test timed out after {timeout}s", timeout)
            return False
        except Exception as e:
            duration = time.time() - start
            self.record_result(test_name, False, f"Exception: {str(e)}", duration)
            return False
    
    async def test_module_1_tenant_management(self):
        """Test Module 1: Tenant Management"""
        print("\n🏢 MODULE 1: TENANT MANAGEMENT REGRESSION")
        print("=" * 70)
        
        tests = [
            ("test_tenant_api_simple.py", "Tenant API Integration"),
            ("test_tenant_crud.py", "Tenant CRUD Operations"),
        ]
        
        module_results = []
        for test_file, test_name in tests:
            if Path(test_file).exists():
                result = await self.run_python_test(test_file, test_name)
                module_results.append(result)
            else:
                self.record_result(test_name, False, "Test file not found")
                module_results.append(False)
        
        success_rate = (sum(module_results) / len(module_results)) * 100 if module_results else 0
        print(f"\nModule 1 Success Rate: {success_rate:.1f}%")
        return success_rate >= 80
    
    async def test_module_2_authentication(self):
        """Test Module 2: Authentication & Token Management"""
        print("\n🔐 MODULE 2: AUTHENTICATION & TOKEN MANAGEMENT REGRESSION")
        print("=" * 70)
        
        tests = [
            ("test_auth_comprehensive.py", "Authentication System"),
            ("test_jwt_direct.py", "JWT Token System"),
            ("test_token_validation.py", "Token Validation"),
        ]
        
        module_results = []
        for test_file, test_name in tests:
            if Path(test_file).exists():
                result = await self.run_python_test(test_file, test_name)
                module_results.append(result)
            else:
                self.record_result(test_name, False, "Test file not found")
                module_results.append(False)
        
        success_rate = (sum(module_results) / len(module_results)) * 100 if module_results else 0
        print(f"\nModule 2 Success Rate: {success_rate:.1f}%")
        return success_rate >= 80
    
    async def test_module_3_user_management(self):
        """Test Module 3: User Management & Service Accounts"""
        print("\n👥 MODULE 3: USER MANAGEMENT & SERVICE ACCOUNTS REGRESSION")
        print("=" * 70)
        
        tests = [
            ("test_user_mgmt_simple.py", "User Management Basic"),
            ("test_user_management_e2e.py", "User Management E2E"),
            ("test_password_reset.py", "Password Reset Workflow"),
            ("test_avatar.py", "Avatar Management"),
            ("test_module3_comprehensive.py", "Module 3 Comprehensive"),
        ]
        
        module_results = []
        for test_file, test_name in tests:
            if Path(test_file).exists():
                result = await self.run_python_test(test_file, test_name)
                module_results.append(result)
            else:
                self.record_result(test_name, False, "Test file not found")
                module_results.append(False)
        
        success_rate = (sum(module_results) / len(module_results)) * 100 if module_results else 0
        print(f"\nModule 3 Success Rate: {success_rate:.1f}%")
        return success_rate >= 80
    
    async def test_integration_across_modules(self):
        """Test Integration Across All Modules"""
        print("\n🔗 CROSS-MODULE INTEGRATION TESTING")
        print("=" * 70)
        
        # Run the most comprehensive test that covers all modules
        result = await self.run_python_test("test_thorough_module3.py", "Thorough System Integration")
        
        return result
    
    async def check_server_health(self):
        """Check server health and basic connectivity"""
        print("\n🏥 SERVER HEALTH CHECK")
        print("=" * 70)
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Test basic connectivity
                start = time.time()
                response = await client.get("http://localhost:8000/health")
                duration = time.time() - start
                
                if response.status_code == 200:
                    health_data = response.json()
                    db_status = health_data.get("checks", {}).get("database", "unknown")
                    self.record_result(
                        "Server Health Check", 
                        True, 
                        f"Status: {health_data.get('status')}, DB: {db_status}", 
                        duration
                    )
                    return True
                else:
                    self.record_result(
                        "Server Health Check", 
                        False, 
                        f"HTTP {response.status_code}", 
                        duration
                    )
                    return False
                    
        except Exception as e:
            self.record_result("Server Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    async def generate_regression_report(self):
        """Generate comprehensive regression test report"""
        total_duration = time.time() - self.start_time
        
        print("\n" + "=" * 80)
        print("📊 COMPLETE REGRESSION TEST REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["passed"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📋 SUMMARY:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {failed_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.1f}s")
        print("-" * 80)
        
        # Categorize by module
        module_categories = {
            "Server Health": [],
            "Module 1 (Tenants)": [],
            "Module 2 (Authentication)": [],
            "Module 3 (Users)": [],
            "Integration": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            categorized = False
            
            if "health" in test_name.lower():
                module_categories["Server Health"].append(result)
            elif any(keyword in test_name.lower() for keyword in ["tenant", "module 1"]):
                module_categories["Module 1 (Tenants)"].append(result)
            elif any(keyword in test_name.lower() for keyword in ["auth", "jwt", "token", "module 2"]):
                module_categories["Module 2 (Authentication)"].append(result)
            elif any(keyword in test_name.lower() for keyword in ["user", "avatar", "password", "module 3"]):
                module_categories["Module 3 (Users)"].append(result)
            else:
                module_categories["Integration"].append(result)
        
        # Print category results
        for category, results in module_categories.items():
            if results:
                category_passed = sum(1 for r in results if r["passed"])
                category_total = len(results)
                category_rate = (category_passed / category_total) * 100
                total_time = sum(r.get("duration", 0) for r in results)
                
                print(f"\n📂 {category}: {category_passed}/{category_total} ({category_rate:.1f}%) - {total_time:.1f}s")
                
                for result in results:
                    status = "✅" if result["passed"] else "❌"
                    duration = f" ({result.get('duration', 0):.2f}s)" if result.get('duration', 0) > 0 else ""
                    print(f"   {status} {result['test']}{duration}")
                    if result.get('details'):
                        print(f"       {result['details']}")
        
        # Failed tests summary
        failed_results = [r for r in self.test_results if not r["passed"]]
        if failed_results:
            print(f"\n⚠️ FAILED TESTS ANALYSIS:")
            print("-" * 50)
            for result in failed_results:
                print(f"❌ {result['test']}")
                if result.get('details'):
                    print(f"   Issue: {result['details']}")
                print(f"   Duration: {result.get('duration', 0):.2f}s")
        
        # Overall assessment
        print("\n" + "=" * 80)
        print("🎯 REGRESSION TEST ASSESSMENT")
        print("=" * 80)
        
        if success_rate >= 95:
            print("🎉 EXCELLENT! All systems are stable and working perfectly.")
            print("   ✅ No regressions detected")
            print("   ✅ All modules functioning correctly") 
            print("   ✅ Ready for continued development")
            assessment = "EXCELLENT"
        elif success_rate >= 85:
            print("✅ VERY GOOD! Systems are mostly stable with minor issues.")
            print("   ✅ Core functionality intact")
            print("   ⚠️ Some minor issues detected")
            print("   ✅ Safe to continue development")
            assessment = "VERY_GOOD"
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE! Core systems working but issues detected.")
            print("   ✅ Basic functionality working")
            print("   ⚠️ Several issues need attention")
            print("   ⚠️ Address issues before major changes")
            assessment = "ACCEPTABLE"
        else:
            print("❌ CRITICAL! Major regressions detected.")
            print("   ❌ Multiple systems failing")
            print("   ❌ Significant regressions present")
            print("   ❌ STOP development and fix issues")
            assessment = "CRITICAL"
        
        print("=" * 80)
        return assessment, success_rate
    
    async def run_complete_regression(self):
        """Run complete regression test suite"""
        self.start_time = time.time()
        
        print("🧪 COMPLETE REGRESSION TEST SUITE")
        print("=" * 80)
        print("Testing all implemented modules for regressions:")
        print("• Module 1: Tenant Management") 
        print("• Module 2: Authentication & Token Management")
        print("• Module 3: User Management & Service Accounts")
        print("• Cross-module integration")
        print("• Server health and connectivity")
        print("=" * 80)
        
        # Run all test suites
        test_suites = [
            ("Server Health", self.check_server_health),
            ("Module 1 Regression", self.test_module_1_tenant_management),
            ("Module 2 Regression", self.test_module_2_authentication),
            ("Module 3 Regression", self.test_module_3_user_management),
            ("Integration Testing", self.test_integration_across_modules),
        ]
        
        suite_results = []
        for suite_name, suite_func in test_suites:
            try:
                print(f"\n🎯 Starting {suite_name}...")
                result = await suite_func()
                suite_results.append((suite_name, result))
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"📊 {suite_name}: {status}")
            except Exception as e:
                print(f"💥 {suite_name}: ERROR - {e}")
                suite_results.append((suite_name, False))
                self.record_result(f"{suite_name} Suite", False, f"Exception: {e}")
        
        # Generate final report
        assessment, success_rate = await self.generate_regression_report()
        
        return assessment, success_rate, suite_results

async def main():
    """Run complete regression testing"""
    print("🚀 Starting Complete Regression Test Suite...")
    print("⏰ This may take several minutes...")
    print()
    
    regression_suite = RegressionTestSuite()
    assessment, success_rate, suite_results = await regression_suite.run_complete_regression()
    
    print(f"\n🏁 REGRESSION TESTING COMPLETE!")
    print(f"📊 Final Assessment: {assessment}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    # Return appropriate exit code
    if success_rate >= 85:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())