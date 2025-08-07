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
def client(override_get_db):
    from src.main import app
    
    app.dependency_overrides[get_db] = override_get_db
    
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
def auth_headers(client, test_user_data):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user_data["email"],
            "password": "Test123!@#"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}

@pytest.fixture
def superadmin_headers(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "admin@sentinel.com",
            "password": "Admin123!@#"
        }
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    return {}