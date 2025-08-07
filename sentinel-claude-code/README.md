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
│   ├── unit/           # Unit tests
│   └── integration/    # Integration tests
├── scripts/            # Utility scripts
├── alembic/           # Database migrations
└── docs/              # Documentation
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

### ✅ Module 1: Tenant Management (Complete)
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
- `POST /api/v1/tenants/{id}/activate` - Activate tenant
- `POST /api/v1/tenants/{id}/deactivate` - Deactivate tenant

### 🚧 Upcoming Modules
- [ ] Module 2: Authentication & Token Management
- [ ] Module 3: User Management (including Service Accounts)
- [ ] Module 4: Role Management
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

### Run all tests
```bash
pytest
```

### Run specific test categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests with coverage
pytest --cov=src --cov-report=html
```

### Test markers
```bash
# Run only tenant tests
pytest -m tenant

# Run only auth tests
pytest -m auth
```

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