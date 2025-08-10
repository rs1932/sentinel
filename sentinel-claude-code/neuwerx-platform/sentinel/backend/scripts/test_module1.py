#!/usr/bin/env python3
"""
Test script for Module 1: Tenant Management
This script tests all aspects of the Tenant module without requiring the full server
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime
from uuid import uuid4
import psycopg2
from psycopg2.extras import RealDictCursor
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Test configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "sentinel_db",
    "user": "postgres",
    "password": "svr967567"  # Update this
}

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ️  {text}{Style.RESET_ALL}")

def print_test(text):
    print(f"  {Fore.BLUE}→ {text}{Style.RESET_ALL}")

class DatabaseTester:
    def __init__(self):
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            print_success("Connected to database")
            return True
        except Exception as e:
            print_error(f"Failed to connect to database: {e}")
            print_info("Make sure PostgreSQL is running and the database exists")
            print_info("Run: ./scripts/setup_database.sh")
            return False
    
    def test_schema(self):
        """Test if the sentinel schema exists"""
        print_test("Testing schema existence...")
        try:
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = 'sentinel'
                );
            """)
            exists = self.cursor.fetchone()['exists']
            if exists:
                print_success("Schema 'sentinel' exists")
                return True
            else:
                print_error("Schema 'sentinel' does not exist")
                return False
        except Exception as e:
            print_error(f"Error checking schema: {e}")
            return False
    
    def test_tables(self):
        """Test if required tables exist"""
        print_test("Testing table existence...")
        required_tables = ['tenants', 'users', 'roles', 'permissions', 'groups']
        
        try:
            self.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'sentinel'
                ORDER BY table_name;
            """)
            tables = [row['table_name'] for row in self.cursor.fetchall()]
            
            print_info(f"Found {len(tables)} tables in sentinel schema")
            
            missing = []
            for table in required_tables:
                if table in tables:
                    print_success(f"Table 'sentinel.{table}' exists")
                else:
                    print_error(f"Table 'sentinel.{table}' is missing")
                    missing.append(table)
            
            return len(missing) == 0
        except Exception as e:
            print_error(f"Error checking tables: {e}")
            return False
    
    def test_tenant_table(self):
        """Test tenant table structure and data"""
        print_test("Testing tenant table structure...")
        
        try:
            # Check columns
            self.cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'sentinel' AND table_name = 'tenants'
                ORDER BY ordinal_position;
            """)
            columns = self.cursor.fetchall()
            
            required_columns = ['id', 'name', 'code', 'type', 'is_active', 'created_at', 'updated_at']
            existing_columns = [col['column_name'] for col in columns]
            
            for req_col in required_columns:
                if req_col in existing_columns:
                    print_success(f"Column '{req_col}' exists")
                else:
                    print_error(f"Column '{req_col}' is missing")
            
            # Check for platform tenant
            self.cursor.execute("""
                SELECT * FROM sentinel.tenants 
                WHERE code = 'PLATFORM';
            """)
            platform_tenant = self.cursor.fetchone()
            
            if platform_tenant:
                print_success(f"Platform tenant exists (ID: {platform_tenant['id']})")
            else:
                print_error("Platform tenant not found")
            
            return True
        except Exception as e:
            print_error(f"Error testing tenant table: {e}")
            return False
    
    def test_crud_operations(self):
        """Test CRUD operations on tenant table"""
        print_test("Testing CRUD operations...")
        
        test_id = str(uuid4())
        test_code = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        try:
            # CREATE
            self.cursor.execute("""
                INSERT INTO sentinel.tenants (
                    id, name, code, type, isolation_mode, 
                    settings, features, tenant_metadata, is_active
                ) VALUES (
                    %s, %s, %s, 'root', 'shared',
                    '{}', '{}', '{}', true
                ) RETURNING id;
            """, (test_id, 'Test Tenant', test_code))
            self.conn.commit()
            print_success(f"Created test tenant (Code: {test_code})")
            
            # READ
            self.cursor.execute("""
                SELECT * FROM sentinel.tenants WHERE id = %s;
            """, (test_id,))
            tenant = self.cursor.fetchone()
            if tenant:
                print_success(f"Read test tenant: {tenant['name']}")
            
            # UPDATE
            self.cursor.execute("""
                UPDATE sentinel.tenants 
                SET name = %s, updated_at = NOW()
                WHERE id = %s;
            """, ('Updated Test Tenant', test_id))
            self.conn.commit()
            print_success("Updated test tenant")
            
            # DELETE
            self.cursor.execute("""
                DELETE FROM sentinel.tenants WHERE id = %s;
            """, (test_id,))
            self.conn.commit()
            print_success("Deleted test tenant")
            
            return True
        except Exception as e:
            print_error(f"CRUD operation failed: {e}")
            self.conn.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print_info("Database connection closed")

class APITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    async def test_server_health(self):
        """Test if the server is running"""
        print_test("Testing server health...")
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Server is {data['status']}")
                    print_info(f"Version: {data['version']}")
                    return True
                else:
                    print_error(f"Server returned status {response.status_code}")
                    return False
        except Exception as e:
            print_error(f"Cannot connect to server: {e}")
            print_info("Make sure the server is running: uvicorn src.main:app --reload")
            return False
    
    async def test_tenant_endpoints(self):
        """Test tenant API endpoints"""
        print_test("Testing tenant API endpoints...")
        import httpx
        
        test_code = f"API-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        created_id = None
        
        try:
            async with httpx.AsyncClient() as client:
                # Test CREATE
                create_data = {
                    "name": "API Test Tenant",
                    "code": test_code,
                    "type": "root",
                    "isolation_mode": "shared",
                    "settings": {"test": True},
                    "features": ["api_access"],
                    "metadata": {"created_by": "test_script"}
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/tenants/",
                    json=create_data
                )
                
                if response.status_code == 201:
                    data = response.json()
                    created_id = data['id']
                    print_success(f"Created tenant via API (ID: {created_id})")
                else:
                    print_error(f"Failed to create tenant: {response.status_code}")
                    print_info(response.text)
                    return False
                
                # Test GET
                response = await client.get(f"{self.base_url}/api/v1/tenants/{created_id}")
                if response.status_code == 200:
                    print_success("Retrieved tenant via API")
                else:
                    print_error(f"Failed to get tenant: {response.status_code}")
                
                # Test LIST
                response = await client.get(f"{self.base_url}/api/v1/tenants/")
                if response.status_code == 200:
                    data = response.json()
                    print_success(f"Listed {data['total']} tenants via API")
                else:
                    print_error(f"Failed to list tenants: {response.status_code}")
                
                # Test UPDATE
                update_data = {"name": "Updated API Test Tenant"}
                response = await client.patch(
                    f"{self.base_url}/api/v1/tenants/{created_id}",
                    json=update_data
                )
                if response.status_code == 200:
                    print_success("Updated tenant via API")
                else:
                    print_error(f"Failed to update tenant: {response.status_code}")
                
                # Test DELETE
                response = await client.delete(f"{self.base_url}/api/v1/tenants/{created_id}")
                if response.status_code == 204:
                    print_success("Deleted tenant via API")
                else:
                    print_error(f"Failed to delete tenant: {response.status_code}")
                
                return True
                
        except Exception as e:
            print_error(f"API test failed: {e}")
            return False

async def run_tests():
    """Run all tests"""
    print_header("SENTINEL MODULE 1 TEST SUITE")
    print_info("Testing Tenant Management Module")
    
    all_passed = True
    
    # Test 1: Database
    print_header("1. DATABASE TESTS")
    db_tester = DatabaseTester()
    
    if db_tester.connect():
        if not db_tester.test_schema():
            all_passed = False
        if not db_tester.test_tables():
            all_passed = False
        if not db_tester.test_tenant_table():
            all_passed = False
        if not db_tester.test_crud_operations():
            all_passed = False
        db_tester.close()
    else:
        all_passed = False
        print_error("Skipping database tests due to connection failure")
    
    # Test 2: API
    print_header("2. API TESTS")
    api_tester = APITester()
    
    if await api_tester.test_server_health():
        if not await api_tester.test_tenant_endpoints():
            all_passed = False
    else:
        print_info("Skipping API tests - server not running")
        print_info("Start server with: uvicorn src.main:app --reload")
    
    # Test 3: Unit Tests
    print_header("3. UNIT TESTS")
    print_test("Running pytest...")
    
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", "tests/unit/test_tenant_service.py", "-v"],
        capture_output=True,
        text=True,
        cwd="/Users/rs/Documents/workspaces/Neuwerx Products/sentinel/sentinel-claude-code"
    )
    
    if result.returncode == 0:
        print_success("Unit tests passed")
    else:
        print_error("Unit tests failed")
        print_info("Run manually: pytest tests/unit/test_tenant_service.py -v")
        all_passed = False
    
    # Summary
    print_header("TEST SUMMARY")
    if all_passed:
        print_success("ALL TESTS PASSED! Module 1 is working correctly.")
        print_info("\nNext steps:")
        print_info("1. Seed sample data: python scripts/seed_tenants.py")
        print_info("2. Explore API: http://localhost:8000/api/docs")
        print_info("3. Proceed to Module 2: Authentication & Token Management")
    else:
        print_error("Some tests failed. Please review the errors above.")
        print_info("\nTroubleshooting:")
        print_info("1. Ensure PostgreSQL is running")
        print_info("2. Run: ./scripts/setup_database.sh")
        print_info("3. Start server: uvicorn src.main:app --reload")
        print_info("4. Check .env file configuration")
    
    return all_passed

if __name__ == "__main__":
    # Check for password argument
    if len(sys.argv) > 1:
        DB_CONFIG["password"] = sys.argv[1]
    else:
        import getpass
        DB_CONFIG["password"] = getpass.getpass("Enter PostgreSQL password: ")
    
    # Run tests
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)