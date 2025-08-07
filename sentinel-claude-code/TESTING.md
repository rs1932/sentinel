# Testing Guide for Sentinel Access Platform

## 🎯 Module 1: Tenant Management Testing

### Prerequisites
1. PostgreSQL installed and running
2. Python 3.10 with virtual environment activated
3. Dependencies installed (`pip install -r requirements.txt`)

### Option 1: Use Your Complete SQL Schema (Recommended)

Since you have a complete SQL schema file (`docs/Sentinel_Schema_All_Tables.sql`), we'll use that to create ALL tables at once:

```bash
# 1. Start PostgreSQL (if not running)
# On macOS:
brew services start postgresql@14

# On Linux:
sudo systemctl start postgresql

# 2. Set up the database with ALL tables
./scripts/setup_database.sh

# Enter your PostgreSQL password when prompted
# This will:
# - Create sentinel_db database
# - Run your complete SQL schema
# - Create all tables in the sentinel schema
```

### Option 2: Use Docker (Alternative)

```bash
# Start all services with Docker
docker-compose up -d

# The docker-compose will automatically:
# - Start PostgreSQL
# - Create the database
# - Run the SQL schema
```

### Testing Module 1

#### Step 1: Verify Database Setup

```bash
# Run the comprehensive test script
python scripts/test_module1.py

# This will test:
# ✓ Database connection
# ✓ Schema existence
# ✓ Table structure
# ✓ CRUD operations
# ✓ API endpoints (if server is running)
# ✓ Unit tests
```

#### Step 2: Start the FastAPI Server

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Copy environment file
cp .env.example .env

# Start the server
uvicorn src.main:app --reload

# Server will be available at:
# - http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

#### Step 3: Test API Endpoints

Open a new terminal and test the endpoints:

```bash
# 1. Check server health
curl http://localhost:8000/health

# 2. Create a tenant
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Company",
    "code": "TEST-001",
    "type": "root",
    "isolation_mode": "shared",
    "settings": {},
    "features": ["api_access"],
    "metadata": {}
  }'

# 3. List all tenants
curl http://localhost:8000/api/v1/tenants/

# 4. Get specific tenant (replace {id} with actual UUID)
curl http://localhost:8000/api/v1/tenants/{id}
```

#### Step 4: Seed Sample Data

```bash
# Add sample tenants for testing
python scripts/seed_tenants.py

# To clear and reseed
python scripts/seed_tenants.py --reseed
```

#### Step 5: Run Automated Tests

```bash
# Run all tests
pytest

# Run only tenant tests
pytest tests/unit/test_tenant_service.py -v
pytest tests/integration/test_tenant_api.py -v

# Run with coverage
pytest --cov=src --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Interactive API Testing

1. Open browser: http://localhost:8000/api/docs
2. Try out the tenant endpoints interactively:
   - `POST /api/v1/tenants/` - Create a new tenant
   - `GET /api/v1/tenants/` - List all tenants
   - `GET /api/v1/tenants/{id}` - Get tenant details
   - `PATCH /api/v1/tenants/{id}` - Update tenant
   - `DELETE /api/v1/tenants/{id}` - Delete tenant
   - `POST /api/v1/tenants/{id}/sub-tenants` - Create sub-tenant
   - `GET /api/v1/tenants/{id}/hierarchy` - Get tenant hierarchy

### Verification Checklist

- [ ] PostgreSQL is running
- [ ] Database `sentinel_db` exists
- [ ] All tables are created in `sentinel` schema
- [ ] Platform tenant exists (ID: 00000000-0000-0000-0000-000000000000)
- [ ] FastAPI server starts without errors
- [ ] API documentation loads at /api/docs
- [ ] Can create a new tenant via API
- [ ] Can list tenants via API
- [ ] Can update tenant via API
- [ ] Can delete tenant via API
- [ ] Unit tests pass
- [ ] Integration tests pass

### Troubleshooting

#### PostgreSQL Connection Issues
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL
brew services start postgresql@14

# Check connection
psql -U postgres -c "SELECT 1"
```

#### Database Issues
```bash
# Connect to PostgreSQL
psql -U postgres

# Check if database exists
\l

# Create database manually if needed
CREATE DATABASE sentinel_db;

# Connect to database
\c sentinel_db

# Check schema
\dn

# Check tables in sentinel schema
\dt sentinel.*
```

#### Python/Server Issues
```bash
# Make sure you're using Python 3.10
python --version

# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check for import errors
python -c "from src.main import app; print('Imports OK')"
```

### What's Working in Module 1

✅ **Database Layer**
- Tenant model with full schema
- Support for root and sub-tenants
- Isolation modes (shared/dedicated)
- Feature flags and settings

✅ **Service Layer**
- Complete CRUD operations
- Business logic validation
- Tenant hierarchy management
- Cache integration (memory/Redis)

✅ **API Layer**
- 10 RESTful endpoints
- OpenAPI documentation
- Error handling
- Request validation

✅ **Testing**
- Unit tests for services
- Integration tests for APIs
- Test fixtures and utilities
- Sample data seeding

### Next Steps

Once Module 1 is verified and working:

1. ✅ Confirm all tests pass
2. ✅ Verify API endpoints work correctly
3. ✅ Ensure database schema is complete
4. 🚀 Proceed to Module 2: Authentication & Token Management

The modular approach ensures each module is fully functional before moving forward. Module 2 will build upon the tenant foundation to add JWT authentication and token management.