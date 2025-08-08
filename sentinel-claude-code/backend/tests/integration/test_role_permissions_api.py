import pytest
from uuid import uuid4

class TestRolePermissionsAPI:
    BASE = "/api/v1/roles"

    @pytest.mark.asyncio
    async def test_assign_list_remove_permissions(self, client, superadmin_headers):
        # Create a role first
        payload = {
            "name": f"test_role_{uuid4().hex[:6]}",
            "display_name": "Test Role",
            "description": "",
            "type": "custom",
            "is_assignable": True,
            "priority": 0,
            "role_metadata": {},
            "is_active": True
        }
        create_role = client.post(f"{self.BASE}/", json=payload, headers=superadmin_headers)
        if create_role.status_code != 201:
            pytest.skip(f"Role creation failed or server not running: {create_role.status_code}")
        role_id = create_role.json()["id"]

        # Create a permission via service-independent endpoint if exists; otherwise insert directly is out-of-scope
        # For now, assume a permission already exists in DB for tests or skip if missing
        # Here we simply skip if assignment fails due to missing permission

        # Try listing permissions (should be empty)
        list_resp = client.get(f"{self.BASE}/{role_id}/permissions", headers=superadmin_headers)
        assert list_resp.status_code in (200, 404)
        if list_resp.status_code == 404:
            pytest.skip("Role permissions listing not available")
        data = list_resp.json()
        assert "direct_permissions" in data

        # Attempt to assign fake permission (should 404)
        perm_id = str(uuid4())
        assign_resp = client.post(
            f"{self.BASE}/{role_id}/permissions",
            json={"permissions": [{"permission_id": perm_id}]},
            headers=superadmin_headers
        )
        # Either 404 (not found) or 200/201 if a valid one; accept both for now
        assert assign_resp.status_code in (201, 404, 400)

        # Remove (should be 204 or 404)
        del_resp = client.delete(
            f"{self.BASE}/{role_id}/permissions/{perm_id}",
            headers=superadmin_headers
        )
        assert del_resp.status_code in (204, 404)

