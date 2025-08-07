# Test Suite Organization

## Directory Structure

```
tests/
├── README.md                   # This file - test organization guide
├── modules/                    # Module-specific comprehensive tests
├── debug/                      # Debug and troubleshooting scripts
├── utils/                      # Utility tests and helper scripts
├── integration/                # Integration tests (existing structure)
└── unit/                       # Unit tests (existing structure)
```

## Module Tests (`modules/`)

### Authentication & Authorization Tests
- `test_auth_comprehensive.py` - Complete authentication system testing
- `test_auth_validate.py` - Authentication validation scenarios
- `test_jwt_direct.py` - Direct JWT token testing
- `test_token_validation.py` - Token validation edge cases

### User Management Tests (Module 3)
- `test_module3_comprehensive.py` - Complete Module 3 functionality
- `test_thorough_module3.py` - Thorough Module 3 validation
- `test_user_management_e2e.py` - End-to-end user workflows
- `test_user_mgmt_direct.py` - Direct user service testing
- `test_user_mgmt_simple.py` - Simplified user management tests
- `test_password_reset.py` - Password reset workflow testing

### Role Management Tests (Module 4)
- `test_role_management_comprehensive.py` - Complete Module 4 functionality
  - **Coverage**: 38 test cases with 100% success rate
  - **Features**: Role CRUD, hierarchy, assignments, validation

### Tenant Management Tests (Module 2)
- `test_tenant_api_simple.py` - Basic tenant API testing
- `test_tenant_crud.py` - Tenant CRUD operations
- `test_tenant_pytest_working.py` - Working tenant test implementation

### System-Wide Tests
- `test_regression_complete.py` - Complete regression testing for modules 1-4
  - **Coverage**: All implemented modules
  - **Success Rate**: 100% across all modules

## Debug Scripts (`debug/`)

### Module-Specific Debugging
- `debug_module4.py` - Role management issue diagnosis
- `debug_login.py` - Authentication troubleshooting
- `debug_user_endpoint.py` - User endpoint debugging

### Usage
```bash
# Run specific debug script
python tests/debug/debug_module4.py

# Debug authentication issues
python tests/debug/debug_login.py
```

## Utility Scripts (`utils/`)

### Test Data Management
- `create_simple_test_user.py` - Create basic test user
- `create_test_user.py` - Create comprehensive test user
- `update_test_user_password.py` - Update test user credentials

### Utility Tests
- `test_avatar.py` - Avatar upload/management testing
- `test_coverage_summary.py` - Test coverage analysis
- `test_metadata_fix.py` - Database metadata validation
- `test_sa_update.py` - Service account update testing
- `run_auth_tests.py` - Authentication test runner

## Test Execution Guide

### Prerequisites
```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Module Tests
```bash
# Complete Module 4 testing (recommended)
python tests/modules/test_role_management_comprehensive.py

# Full system regression testing
python tests/modules/test_regression_complete.py

# Module 3 comprehensive testing
python tests/modules/test_module3_comprehensive.py
```

### Running Debug Scripts
```bash
# Debug specific Module 4 issues
python tests/debug/debug_module4.py

# Troubleshoot authentication
python tests/debug/debug_login.py
```

### Using Utility Scripts
```bash
# Create test user for manual testing
python tests/utils/create_test_user.py

# Reset test user password
python tests/utils/update_test_user_password.py
```

## Test Standards

### Success Criteria
- **95-100%**: Production ready
- **85-94%**: Very good, minor issues
- **70-84%**: Good, needs attention
- **<70%**: Significant issues

### Current Status
- **Module 1 (Auth)**: 100% ✅
- **Module 2 (Tenants)**: 100% ✅
- **Module 3 (Users)**: 100% ✅
- **Module 4 (Roles)**: 100% ✅

### Test Data
- **Email**: test@example.com
- **Password**: password123
- **Tenant**: TEST
- **Base URL**: http://localhost:8000/api/v1

## Integration with Existing Tests

The organized tests work alongside the existing pytest structure:

- `integration/` - API integration tests with pytest
- `unit/` - Service and utility unit tests with pytest
- `modules/` - Comprehensive module testing (new organization)
- `debug/` - Troubleshooting tools (new organization)
- `utils/` - Test utilities and helpers (new organization)

## Best Practices

1. **Run comprehensive tests** before making system changes
2. **Use debug scripts** to troubleshoot specific issues
3. **Execute regression tests** after module completion
4. **Maintain test data isolation** with timestamps
5. **Clean up test resources** after execution

## Documentation References

- **Test Methodology**: `docs/testing/TEST_METHODOLOGY.md`
- **Testing Guide**: `docs/testing/TESTING.md`
- **API Endpoints**: `docs/project/API_ENDPOINTS.md`
- **Task Progress**: `docs/project/TASK_LIST.md`