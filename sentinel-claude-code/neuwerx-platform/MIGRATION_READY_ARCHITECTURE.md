# Migration-Ready Architecture Guide

## 🎯 Overview

This architecture is designed for **Option 1 (Unified Server)** with an **easy migration path to Option 2 (Separate Services)**. Every design decision prioritizes clean separation and minimal coupling between domains.

## 📁 Current Directory Structure

```
neuwerx-platform/
├── api/                           # 🔄 Unified API Server
│   ├── src/
│   │   ├── main.py               # Single entry point for all services
│   │   └── v1/
│   │       ├── sentinel/         # Sentinel RBAC domain
│   │       │   ├── api/          # Route handlers
│   │       │   ├── services/     # Business logic
│   │       │   ├── models/       # Data models
│   │       │   ├── schemas/      # API schemas
│   │       │   └── middleware/   # Domain-specific middleware
│   │       └── metamorphic/      # Future: Metamorphic fields domain
│   ├── requirements.txt          # API server dependencies
│   └── .env                      # Configuration
├── shared/                       # 🔗 Common Utilities
│   ├── auth/                     # Authentication dependencies
│   ├── config/                   # Modular configuration
│   └── database/                 # Database connection management
├── sentinel/                     # 📚 Legacy Structure (keep for reference)
├── metamorphic/                  # 🚀 Future: Field management system
└── docs/                         # 📖 Documentation
```

## 🏗️ Migration-Friendly Design Principles

### 1. **Domain Separation**
- ✅ Sentinel and Metamorphic code never directly import each other
- ✅ Each domain has its own services, models, and schemas
- ✅ Cross-domain communication uses well-defined interfaces

### 2. **Shared Infrastructure**
- ✅ Common utilities (auth, database, config) are in `shared/`
- ✅ Shared components have stable interfaces
- ✅ Easy to duplicate shared code for separate services later

### 3. **Clean API Structure**  
- ✅ Routes prefixed by domain: `/api/v1/sentinel/*` and `/api/v1/metamorphic/*`
- ✅ Each domain can become its own FastAPI app easily
- ✅ No cross-domain route dependencies

### 4. **Modular Configuration**
- ✅ `SentinelConfig` and `MetamorphicConfig` classes
- ✅ Easy to split into separate `.env` files
- ✅ Unified settings for current deployment, separable for future

## 🚀 How to Migrate to Separate Services (When Ready)

### Step 1: Extract Sentinel Service (30 minutes)
```bash
# Create new Sentinel service directory
mkdir sentinel-service/
cp -r api/src/v1/sentinel/* sentinel-service/src/
cp shared/ sentinel-service/shared/

# Update imports in sentinel-service/src/main.py:
# from shared.config import SentinelConfig
# settings = SentinelConfig()

# Update API routes to remove /sentinel prefix
# /api/v1/sentinel/users -> /api/v1/users
```

### Step 2: Extract Metamorphic Service (30 minutes)  
```bash
# Similar process for Metamorphic
mkdir metamorphic-service/
cp -r api/src/v1/metamorphic/* metamorphic-service/src/
cp shared/ metamorphic-service/shared/
```

### Step 3: Update Cross-Domain Communication (1-2 hours)
```python
# Change from direct imports:
from api.v1.sentinel.services import UserService

# To HTTP API calls:
async def get_user(user_id: str):
    response = await httpx.get(f"http://sentinel-service/api/v1/users/{user_id}")
    return response.json()
```

### Step 4: Deploy Separately (1 hour)
```yaml
# docker-compose.yml
services:
  sentinel:
    build: ./sentinel-service
    ports: ["8000:8000"]
  
  metamorphic:
    build: ./metamorphic-service  
    ports: ["8001:8001"]
    
  api-gateway:
    image: nginx
    # Route /sentinel/* -> sentinel:8000
    # Route /metamorphic/* -> metamorphic:8001
```

## 🔧 Key Interfaces for Migration

### Authentication Interface
```python
# Current: Direct function calls
user = await auth_service.get_current_user(token, db)

# Future: HTTP API calls  
user = await http_client.get("/sentinel/auth/verify", headers={"Authorization": f"Bearer {token}"})
```

### Permission Interface  
```python
# Current: Direct service calls
has_permission = await permission_service.check_permission(user_id, "read_fields")

# Future: HTTP API calls
response = await http_client.post("/sentinel/permissions/check", json={"user_id": user_id, "permission": "read_fields"})
has_permission = response.json()["allowed"]
```

### Database Interface
```python
# Current: Shared database connection
with db_manager.get_session() as session:
    # Both services use same connection

# Future: Separate databases
# Sentinel: postgres://localhost/sentinel_db  
# Metamorphic: postgres://localhost/metamorphic_db
```

## 📊 Migration Effort Estimate

| Task | Unified → Separate | Time |
|------|-------------------|------|
| Extract service code | Copy/paste + import fixes | 1-2 hours |
| Update cross-domain calls | Replace imports with HTTP | 2-4 hours |
| Database separation | Split schemas/connections | 1-2 hours |
| Configuration updates | Split .env files | 30 minutes |
| Deployment updates | Docker/K8s configs | 1-2 hours |
| Testing | Integration tests | 2-4 hours |
| **Total** | | **8-15 hours** |

## 🎯 Current Status

### ✅ Completed
- [x] Shared utilities (auth, config, database)
- [x] Unified API server structure
- [x] Domain separation architecture
- [x] Migration-ready interfaces

### 🚧 In Progress  
- [ ] Migrate existing Sentinel routes to new structure
- [ ] Create Metamorphic domain structure
- [ ] Add cross-domain interfaces

### 📋 Next Steps
1. **Migrate existing Sentinel routes** from `sentinel/backend/src/api/v1/` to `api/src/v1/sentinel/`
2. **Test unified server** with migrated routes
3. **Create Metamorphic domain** structure and basic field management
4. **Add cross-domain authentication** between Sentinel and Metamorphic

## 🔍 How to Test Current Structure

```bash
# Test configuration loading
cd neuwerx-platform/api/src
python3 -c "
import sys
sys.path.append('../..')
from shared.config import get_settings
settings = get_settings()
print(f'Config loaded: {settings.APP_NAME}')
"

# Test unified server (when routes are migrated)
cd neuwerx-platform/api/src  
uvicorn main:app --reload
# Visit: http://localhost:8000/api/v1/sentinel/health
```

This architecture gives you all the benefits of unified development now, while maintaining a clear and easy path to microservices later! 🚀