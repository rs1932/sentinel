# Sentinel Access Platform

An enterprise-grade, API-based multi-tenant access control system providing granular permission management from product family level down to individual field access.

## 🚀 Quick Start

### Prerequisites
- Python 3.10 (IMPORTANT: Not 3.11 or 3.12)
- PostgreSQL 15+
- Redis (optional, disabled by default)
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd sentinel-claude-code
```

2. **Set up Python environment**
```bash
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Set up database**
```bash
# Create database
createdb sentinel_db

# Run migrations
alembic upgrade head

# Seed sample data (optional)
python scripts/seed_tenants.py
```

5. **Run the application**
```bash
uvicorn src.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Docker Setup

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec sentinel-api alembic upgrade head

# Seed data
docker-compose exec sentinel-api python scripts/seed_tenants.py
```

## 📁 Project Structure

```
sentinel-platform/
├── src/
│   ├── api/v1/          # API endpoints
│   ├── core/            # Core business logic
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic services
│   ├── middleware/      # FastAPI middleware
│   ├── utils/           # Utility functions
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   └── main.py          # FastAPI app
├── tests/
│   ├── modules/         # Module-specific comprehensive tests
│   ├── debug/           # Debug and troubleshooting scripts
│   ├── utils/           # Test utilities and helpers
│   ├── unit/            # Unit tests
│   └── integration/     # Integration tests
├── docs/
│   ├── project/         # Project management and API documentation
│   ├── testing/         # Testing methodologies and guides
│   └── [existing docs]  # Specifications and implementation notes
├── scripts/             # Database and utility scripts
├── alembic/            # Database migrations
└── storage/            # File storage (avatars, uploads)
```

## 🔌 Module Status

### ✅ Phase 0: Foundation (Complete)
- [x] Directory structure
- [x] Python 3.10 environment
- [x] Dependencies installation
- [x] Base configuration
- [x] Database connection with sentinel schema
- [x] Base model with timestamps
- [x] Alembic setup
- [x] Error handling framework
- [x] Docker configuration
- [x] Test configuration
- [x] Cache service (memory/Redis)

### ✅ Module 1: Authentication & JWT Token Management (Complete)
- [x] Database model
- [x] Pydantic schemas
- [x] Service layer with business logic
- [x] RESTful API endpoints
- [x] Database migrations
- [x] Unit and integration tests
- [x] Sample data script

**Features:**
- JWT token generation and validation
- Refresh token rotation
- Token blacklisting for logout
- Multi-tenant authentication
- Session management
- Service account authentication

**API Endpoints:**
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/service-account/login` - Service account login
- `GET /api/v1/auth/verify` - Token verification

### ✅ Module 2: Tenant Management (Complete)
- [x] Database model
- [x] Pydantic schemas
- [x] Service layer with business logic
- [x] RESTful API endpoints
- [x] Database migrations
- [x] Unit and integration tests
- [x] Sample data script

**Features:**
- Multi-tenant support with sub-tenants
- Tenant isolation modes (shared/dedicated)
- Tenant hierarchy management
- Feature flags per tenant
- Tenant activation/deactivation
- Comprehensive validation

**API Endpoints:**
- `POST /api/v1/tenants/` - Create tenant
- `GET /api/v1/tenants/` - List tenants
- `GET /api/v1/tenants/{id}` - Get tenant details
- `PATCH /api/v1/tenants/{id}` - Update tenant
- `DELETE /api/v1/tenants/{id}` - Delete tenant
- `POST /api/v1/tenants/{id}/sub-tenants` - Create sub-tenant
- `GET /api/v1/tenants/{id}/hierarchy` - Get tenant hierarchy

### ✅ Module 3: User Management (Complete)
- [x] Database model
- [x] Pydantic schemas
- [x] Service layer with business logic
- [x] RESTful API endpoints
- [x] Database migrations
- [x] Password reset functionality
- [x] Avatar upload support
- [x] Comprehensive testing

**Features:**
- User CRUD operations
- Profile management with avatars
- Password reset with email tokens
- Service account management
- User activation/deactivation
- Multi-tenant user isolation

**API Endpoints:**
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/` - List users
- `GET /api/v1/users/{id}` - Get user details
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `POST /api/v1/users/{id}/avatar` - Upload avatar
- `POST /api/v1/password-reset/request` - Request password reset
- `POST /api/v1/password-reset/confirm` - Confirm password reset

### ✅ Module 4: Role Management (Complete)
- [x] Database model with hierarchy support
- [x] Pydantic schemas
- [x] Service layer with business logic
- [x] RESTful API endpoints
- [x] Database migrations
- [x] Role hierarchy validation
- [x] User-role assignments
- [x] Comprehensive testing (100% success rate)

**Features:**
- Role CRUD operations
- Hierarchical role structure
- Role inheritance
- User-role assignments
- Circular dependency prevention
- Role validation
- System and custom roles

**API Endpoints:**
- `POST /api/v1/roles/` - Create role
- `GET /api/v1/roles/` - List roles
- `GET /api/v1/roles/{id}` - Get role details
- `PATCH /api/v1/roles/{id}` - Update role
- `DELETE /api/v1/roles/{id}` - Delete role
- `GET /api/v1/roles/{id}/hierarchy` - Get role hierarchy
- `POST /api/v1/roles/{id}/users` - Assign role to user
- `POST /api/v1/roles/validate` - Validate role hierarchy

### 🚧 Upcoming Modules
- [ ] Module 5: Group Management
- [ ] Module 6: Permission Management
- [ ] Module 7: Resource Management
- [ ] Module 8: Field Definitions
- [ ] Module 9: Navigation/Menu
- [ ] Module 10: Approval Chains
- [ ] Module 11: Permission Evaluation & Cache
- [ ] Module 12: Audit & Compliance
- [ ] Module 13: Health & Monitoring
- [ ] Module 14: AI & Intelligence Features

## 🧪 Testing

### Comprehensive Module Tests (Recommended)
```bash
# Module 4: Complete role management testing (100% success rate)
python tests/modules/test_role_management_comprehensive.py

# Full system regression testing (modules 1-4)
python tests/modules/test_regression_complete.py

# Module 3: User management testing
python tests/modules/test_module3_comprehensive.py
```

### Unit and Integration Tests
```bash
# Run all pytest tests
pytest

# Unit tests only  
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests with coverage
pytest --cov=src --cov-report=html
```

### Debug and Utilities
```bash
# Debug specific module issues
python tests/debug/debug_module4.py

# Create test user for manual testing
python tests/utils/create_test_user.py

# Test utilities and helpers
python tests/utils/test_coverage_summary.py
```

### Test Organization
- **`tests/modules/`** - Comprehensive module testing suites
- **`tests/debug/`** - Debug scripts for troubleshooting
- **`tests/utils/`** - Test utilities and helper scripts
- **`tests/unit/`** - Unit tests with pytest
- **`tests/integration/`** - API integration tests

See `tests/README.md` and `docs/testing/TEST_METHODOLOGY.md` for detailed testing documentation.

## 🔧 Development

### Database Migrations
```bash
# Create new migration
alembic revision -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## 📝 API Documentation

When running in development mode, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- Attribute-based access control (ABAC)
- Field-level permissions
- Multi-factor authentication support
- Service account management
- Rate limiting
- Audit logging

## 🚀 Deployment

### Environment Variables
See `.env.example` for all available configuration options.

### Production Recommendations
1. Use strong JWT secret key
2. Enable Redis for caching
3. Configure proper database pooling
4. Set up SSL/TLS
5. Enable rate limiting
6. Configure proper CORS origins
7. Use environment-specific settings
8. Set up monitoring and logging

## 📄 License

[License Type] - See LICENSE file for details

## 👥 Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## 📞 Support

For support, please contact the development team or open an issue in the project repository.