#!/usr/bin/env python3
"""
Convenient script to run authentication tests with fixed imports and Allure reporting
"""
import os
import sys
import subprocess

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_tests():
    """Run authentication tests with Allure reporting"""
    
    print("🧪 Running Authentication Module Tests with Allure Reporting")
    print("=" * 60)
    
    # Ensure we're in the correct directory
    os.chdir(project_root)
    
    # Run tests
    test_files = [
        "tests/unit/test_password_utils_allure.py",
        "tests/unit/test_jwt_utils_allure.py"
    ]
    
    cmd = [
        sys.executable, "-m", "pytest",
        *test_files,
        "-v",
        "--alluredir=./allure-results",
        "--clean-alluredir",
        "--tb=short"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)
    
    # Run the tests
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print("\n✅ Tests completed successfully!")
        
        # Generate Allure report
        print("\n📊 Generating Allure report...")
        subprocess.run([
            "allure", "generate", "allure-results",
            "--clean", "-o", "allure-report"
        ])
        
        print("📈 Allure report generated in './allure-report'")
        print("🌐 To view report: allure serve allure-results")
        
    else:
        print("\n❌ Some tests failed. Check the output above.")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)