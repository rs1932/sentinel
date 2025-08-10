# Sentinel Platform

A comprehensive multi-tenant RBAC (Role-Based Access Control) system with a modern React frontend and FastAPI backend.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 12+
- Git

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE sentinel_dev;
```

2. Run the database schema (if not already done):
```bash
psql -d sentinel_dev -U postgres -f docs/sentinel/Sentinel_Schema_All_Tables.sql
```

### Easy Startup & Management

#### Start Services

```bash
# Start both services
./start.sh

# Start only backend
./start.sh backend

# Start only frontend  
./start.sh frontend

# Start both explicitly
./start.sh both
```

#### Stop Services

```bash
# Stop both services
./stop.sh

# Stop only backend
./stop.sh backend

# Stop only frontend
./stop.sh frontend

# Stop both explicitly
./stop.sh both
```

#### Features

**Start Script (`start.sh`)**:
- ✅ Port availability checking (exits if ports are in use)
- ✅ Selective service startup (backend, frontend, or both)
- ✅ Virtual environment and dependency validation
- ✅ Automatic uvicorn and npm dependency installation
- ✅ Color-coded output with service prefixes
- ✅ Clear status display with URLs and credentials
- ✅ Graceful shutdown with Ctrl+C

**Stop Script (`stop.sh`)**:
- ✅ Selective service stopping (backend, frontend, or both)
- ✅ Multiple kill strategies (by port, by process pattern)
- ✅ Graceful shutdown attempt before force kill
- ✅ Process verification and status reporting
- ✅ Port availability confirmation

### Manual Setup

If you prefer to start services manually:

#### Backend
```bash
cd neuwerx-platform
source venv/bin/activate
cd api
uvicorn src.v1.sentinel.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Frontend
```bash
cd neuwerx-platform/sentinel/frontend
npm install
npm run dev
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/v1/sentinel/docs

## Default Credentials

### Platform Admin (Super Admin)
- **Email**: admin@sentinel.com
- **Password**: admin123
- **Tenant**: PLATFORM

### Maritime Admin (Tenant Admin)
- **Email**: maritimeadmin@maritime.com
- **Password**: admin123
- **Tenant**: MARITIME

## Project Structure

```
neuwerx-platform/
├── start.sh                    # Easy startup script
├── requirements.txt            # Python dependencies
├── api/                        # Backend FastAPI application
│   └── src/v1/sentinel/        # Sentinel API v1
│       ├── main.py             # FastAPI app entry point
│       ├── routes/             # API endpoints
│       ├── services/           # Business logic
│       ├── models/             # Database models
│       └── schemas/            # Pydantic schemas
├── sentinel/
│   └── frontend/               # Next.js React frontend
│       ├── src/
│       │   ├── app/            # Next.js app router
│       │   ├── components/     # React components
│       │   ├── store/          # Zustand state management
│       │   └── lib/            # Utilities and API client
│       └── package.json
└── docs/                       # Documentation
```

## Development

### Backend Development

The backend uses:
- **FastAPI** for API framework
- **SQLAlchemy** for ORM
- **PostgreSQL** for database
- **JWT** for authentication
- **Dynamic RBAC** for permissions

### Frontend Development

The frontend uses:
- **Next.js 15** with App Router
- **React 18** with TypeScript
- **Tailwind CSS** for styling
- **shadcn/ui** for components
- **Zustand** for state management

### Admin Access Control

Sentinel UI is restricted to users with admin permissions:
- `user:admin` - User management admin
- `tenant:admin` - Tenant management admin  
- `role:admin` - Role management admin

Users need at least one of these permissions to access the system.

## Features

- 🔐 **Multi-tenant Architecture** with tenant isolation
- 👥 **Dynamic RBAC System** with database-driven permissions
- 🎯 **Admin-only Access Control** for security
- 🔑 **JWT Authentication** with refresh tokens
- 📊 **Comprehensive User Management** with bulk operations
- 🏢 **Tenant Management** with hierarchy support
- 🛠️ **Developer-friendly** with debug tools and API documentation
- 🎨 **Modern UI** with responsive design

## Support

For issues or questions, check the documentation in the `docs/` directory or refer to the API documentation at `/docs` when the server is running.