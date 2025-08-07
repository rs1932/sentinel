import pytest
import asyncio
import sys
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import uuid
from unittest.mock import patch

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment variable to use correct database password before importing config
os.environ["DATABASE_URL"] = "postgresql://postgres:svr967567@localhost:5432/sentinel_db"

from src.database import Base, get_db
from src.config import settings

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def test_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # For SQLite tests, create tables without schema
    # Temporarily remove schema from metadata
    original_schema = Base.metadata.schema
    Base.metadata.schema = None
    
    # Also need to temporarily remove schema from table definitions
    for table in Base.metadata.tables.values():
        table.schema = None
    
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)
    
    # Restore original schema
    Base.metadata.schema = original_schema
    for table in Base.metadata.tables.values():
        table.schema = original_schema

@pytest.fixture(scope="function")
def test_session(test_engine):
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def override_get_db(test_session):
    def _override_get_db():
        try:
            yield test_session
        finally:
            pass
    return _override_get_db

@pytest.fixture(scope="function")
def client(override_get_db, test_session):
    from src.main import app
    from src.models.tenant import Tenant
    from src.models.user import User
    from src.utils.password import PasswordManager
    from uuid import uuid4, UUID
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test tenant and users for authentication
    password_manager = PasswordManager()
    
    # Create platform tenant
    platform_tenant = Tenant(
        id=UUID("00000000-0000-0000-0000-000000000000"),
        name="Sentinel Platform",
        code="PLATFORM", 
        type="root",
        isolation_mode="dedicated",
        is_active=True,
        settings={"is_platform_tenant": True},
        features=[],
        metadata={}
    )
    test_session.add(platform_tenant)
    
    # Create test tenant
    test_tenant = Tenant(
        id=UUID("f3c417f3-d9f6-44e6-912a-442e02f15e15"),
        name="Test Company",
        code="TEST",
        type="root", 
        isolation_mode="shared",
        is_active=True,
        settings={"max_users": 100},
        features=["authentication", "user_management"],
        metadata={}
    )
    test_session.add(test_tenant)
    
    # Create admin user
    admin_user = User(
        id=uuid4(),
        tenant_id=platform_tenant.id,
        email="admin@sentinel.com",
        username="admin",
        password_hash=password_manager.hash_password("Admin123!@#"),
        is_service_account=False,
        is_active=True
    )
    test_session.add(admin_user)
    
    # Create regular test user
    test_user = User(
        id=uuid4(),
        tenant_id=test_tenant.id,
        email="test@example.com",
        username="testuser",
        password_hash=password_manager.hash_password("password123"),
        is_service_account=False,
        is_active=True
    )
    test_session.add(test_user)
    
    test_session.commit()
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_tenant_id():
    return str(uuid.uuid4())

@pytest.fixture
def test_user_id():
    return str(uuid.uuid4())

@pytest.fixture
def test_tenant_data(test_tenant_id):
    return {
        "id": test_tenant_id,
        "name": "Test Company",
        "code": "TEST-001",
        "type": "root",
        "isolation_mode": "shared",
        "is_active": True,
        "settings": {},
        "features": [],
        "metadata": {}
    }

@pytest.fixture
def test_user_data(test_user_id, test_tenant_id):
    return {
        "id": test_user_id,
        "tenant_id": test_tenant_id,
        "email": "test@example.com",
        "username": "testuser",
        "is_service_account": False,
        "is_active": True,
        "attributes": {},
        "preferences": {}
    }

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for regular user with read permissions"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "test@example.com",
            "password": "password123",
            "tenant_code": "TEST"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture
def superadmin_headers(client):
    """Get authentication headers for superadmin with full permissions"""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@sentinel.com",
            "password": "Admin123!@#",
            "tenant_code": "PLATFORM"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture
def service_account_headers(client):
    """Get authentication headers for service account with admin permissions"""
    response = client.post(
        "/api/v1/auth/token",
        json={
            "client_id": "service@example.com",
            "client_secret": "test-service-key-123",
            "scope": "tenant:read tenant:write tenant:admin"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

def get_auth_token(client, credentials: dict) -> str:
    """Helper function to get authentication token"""
    if "client_id" in credentials:
        # Service account login
        response = client.post("/api/v1/auth/token", json=credentials)
    else:
        # Regular user login
        response = client.post("/api/v1/auth/login", json=credentials)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    
    raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

def get_auth_headers(token: str) -> dict:
    """Helper function to format authentication headers"""
    return {"Authorization": f"Bearer {token}"}