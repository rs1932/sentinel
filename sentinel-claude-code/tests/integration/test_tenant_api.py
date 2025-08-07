import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient
from uuid import uuid4

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.models.tenant import TenantType, IsolationMode

@pytest.mark.integration
@pytest.mark.tenant
class TestTenantAPI:
    
    def test_create_tenant(self, client: TestClient, superadmin_headers: dict):
        tenant_data = {
            "name": "Test Company",
            "code": "TEST-001",
            "type": "root",
            "isolation_mode": "shared",
            "settings": {"theme": "light"},
            "features": ["api_access", "sso"],
            "metadata": {"industry": "technology"}
        }
        
        response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == tenant_data["name"]
        assert data["code"] == tenant_data["code"]
        assert data["type"] == tenant_data["type"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_tenant_duplicate_code(self, client: TestClient, superadmin_headers: dict):
        tenant_data = {
            "name": "First Company",
            "code": "DUP-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        response1 = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert response1.status_code == 201
        
        tenant_data["name"] = "Second Company"
        response2 = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["error"]["message"]
    
    def test_get_tenant(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenant_data = {
            "name": "Get Test Company",
            "code": "GET-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]
        
        get_response = client.get(f"/api/v1/tenants/{tenant_id}", headers=auth_headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == tenant_id
        assert data["name"] == tenant_data["name"]
        assert data["code"] == tenant_data["code"]
        assert "sub_tenants_count" in data
        assert "users_count" in data
        assert "hierarchy" in data
    
    def test_get_tenant_not_found(self, client: TestClient, auth_headers: dict):
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/tenants/{fake_id}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_tenant_by_code(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenant_data = {
            "name": "Code Test Company",
            "code": "CODE-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert create_response.status_code == 201
        
        get_response = client.get(f"/api/v1/tenants/code/{tenant_data['code']}", headers=auth_headers)
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["code"] == tenant_data["code"]
        assert data["name"] == tenant_data["name"]
    
    def test_list_tenants(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenants_data = [
            {"name": "List Test 1", "code": "LIST-001", "type": "root", "isolation_mode": "shared"},
            {"name": "List Test 2", "code": "LIST-002", "type": "root", "isolation_mode": "shared"},
            {"name": "List Test 3", "code": "LIST-003", "type": "root", "isolation_mode": "dedicated"}
        ]
        
        for tenant_data in tenants_data:
            response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
            assert response.status_code == 201
        
        list_response = client.get("/api/v1/tenants/", headers=auth_headers)
        assert list_response.status_code == 200
        data = list_response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["items"]) >= 3
    
    def test_list_tenants_with_filters(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenant_data = {
            "name": "Filter Test Company",
            "code": "FILTER-001",
            "type": "root",
            "isolation_mode": "dedicated"
        }
        
        client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        
        response = client.get("/api/v1/tenants/?name=Filter", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert all("Filter" in item["name"] for item in data["items"])
    
    def test_update_tenant(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenant_data = {
            "name": "Update Test Company",
            "code": "UPDATE-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]
        
        update_data = {
            "name": "Updated Company Name",
            "settings": {"theme": "dark"},
            "features": ["multi_factor_auth", "api_access"]
        }
        
        update_response = client.patch(f"/api/v1/tenants/{tenant_id}", json=update_data, headers=auth_headers)
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == update_data["name"]
        assert data["settings"] == update_data["settings"]
        assert data["features"] == update_data["features"]
        assert data["code"] == tenant_data["code"]
    
    def test_delete_tenant(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        tenant_data = {
            "name": "Delete Test Company",
            "code": "DELETE-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]
        
        delete_response = client.delete(f"/api/v1/tenants/{tenant_id}", headers=superadmin_headers)
        assert delete_response.status_code == 204
        
        get_response = client.get(f"/api/v1/tenants/{tenant_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_create_sub_tenant(self, client: TestClient, superadmin_headers: dict):
        parent_data = {
            "name": "Parent Company",
            "code": "PARENT-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        parent_response = client.post("/api/v1/tenants/", json=parent_data, headers=superadmin_headers)
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]
        
        sub_tenant_data = {
            "name": "Sub Company",
            "code": "SUB-001",
            "isolation_mode": "shared",
            "settings": {},
            "features": [],
            "metadata": {}
        }
        
        sub_response = client.post(f"/api/v1/tenants/{parent_id}/sub-tenants", json=sub_tenant_data, headers=superadmin_headers)
        assert sub_response.status_code == 201
        data = sub_response.json()
        assert data["name"] == sub_tenant_data["name"]
        assert data["code"] == sub_tenant_data["code"]
        assert data["type"] == "sub_tenant"
        assert data["parent_tenant_id"] == parent_id
    
    def test_activate_deactivate_tenant(self, client: TestClient, superadmin_headers: dict):
        tenant_data = {
            "name": "Toggle Test Company",
            "code": "TOGGLE-001",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        create_response = client.post("/api/v1/tenants/", json=tenant_data, headers=superadmin_headers)
        assert create_response.status_code == 201
        tenant_id = create_response.json()["id"]
        
        deactivate_response = client.post(f"/api/v1/tenants/{tenant_id}/deactivate", headers=superadmin_headers)
        assert deactivate_response.status_code == 200
        assert deactivate_response.json()["is_active"] is False
        
        activate_response = client.post(f"/api/v1/tenants/{tenant_id}/activate", headers=superadmin_headers)
        assert activate_response.status_code == 200
        assert activate_response.json()["is_active"] is True
    
    def test_get_tenant_hierarchy(self, client: TestClient, superadmin_headers: dict, auth_headers: dict):
        parent_data = {
            "name": "Hierarchy Parent",
            "code": "HIER-PARENT",
            "type": "root",
            "isolation_mode": "shared"
        }
        
        parent_response = client.post("/api/v1/tenants/", json=parent_data, headers=superadmin_headers)
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]
        
        sub_tenant_data = {
            "name": "Hierarchy Child",
            "code": "HIER-CHILD",
            "isolation_mode": "shared",
            "settings": {},
            "features": [],
            "metadata": {}
        }
        
        sub_response = client.post(f"/api/v1/tenants/{parent_id}/sub-tenants", json=sub_tenant_data, headers=superadmin_headers)
        assert sub_response.status_code == 201
        sub_id = sub_response.json()["id"]
        
        hierarchy_response = client.get(f"/api/v1/tenants/{sub_id}/hierarchy", headers=auth_headers)
        assert hierarchy_response.status_code == 200
        hierarchy = hierarchy_response.json()
        assert len(hierarchy) == 2
        assert hierarchy[0]["id"] == parent_id
        assert hierarchy[1]["id"] == sub_id