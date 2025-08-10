import pytest
import httpx
from uuid import uuid4

BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = f"{BASE_URL}/auth/login"
GROUP_URL = f"{BASE_URL}/groups"
USERS_URL = f"{BASE_URL}/users"
ROLES_URL = f"{BASE_URL}/roles"

TEST_USER = {
    "email": "admin@sentinel.com",
    "password": "admin123",
    "tenant_code": "PLATFORM"
}

@pytest.mark.asyncio
async def test_group_http_endpoints_full_flow():
    async with httpx.AsyncClient() as client:
        # 0) Authenticate
        auth = await client.post(AUTH_URL, json=TEST_USER)
        if auth.status_code != 200:
            pytest.skip(f"Auth failed (server not running or seed missing): {auth.status_code}")
        token = auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1) Create group
        g_payload = {
            "name": f"grp_{uuid4().hex[:6]}",
            "display_name": "HTTP Group",
            "description": "HTTP test",
            "metadata": {"env": "test"},
            "is_active": True
        }
        g_res = await client.post(f"{GROUP_URL}/", json=g_payload, headers=headers)
        assert g_res.status_code in (200, 201), g_res.text
        group = g_res.json()
        group_id = group["id"]

        # 2) List & Get
        l_res = await client.get(f"{GROUP_URL}/", headers=headers)
        assert l_res.status_code == 200
        get_res = await client.get(f"{GROUP_URL}/{group_id}", headers=headers)
        assert get_res.status_code == 200

        # 3) Update
        u_res = await client.patch(f"{GROUP_URL}/{group_id}", json={"display_name": "HTTP Group Updated"}, headers=headers)
        assert u_res.status_code == 200
        assert u_res.json()["display_name"] == "HTTP Group Updated"

        # 4) Create a user to add to group
        new_user_payload = {
            "email": f"grp-user-{uuid4().hex[:6]}@example.com",
            "username": f"grpuser_{uuid4().hex[:6]}",
            "password": "TempPass123!",
            "is_active": True
        }
        user_res = await client.post(f"{USERS_URL}/", json=new_user_payload, headers=headers)
        assert user_res.status_code in (200, 201), user_res.text
        user_id = user_res.json()["id"]

        # 5) Add user to group, list members, then remove
        add_req = {"user_ids": [user_id]}
        add_res = await client.post(f"{GROUP_URL}/{group_id}/users", json=add_req, headers=headers)
        assert add_res.status_code in (200, 201), add_res.text
        lm_res = await client.get(f"{GROUP_URL}/{group_id}/users", headers=headers)
        assert lm_res.status_code == 200 and user_id in set(lm_res.json())
        rem_res = await client.delete(f"{GROUP_URL}/{group_id}/users/{user_id}", headers=headers)
        assert rem_res.status_code in (200, 204)

        # 6) Create role, assign to group, list roles, then remove
        role_payload = {
            "name": f"grp_role_{uuid4().hex[:6]}",
            "display_name": "Group Role",
            "description": "Role for group test",
            "type": "custom",
            "is_assignable": True,
            "priority": 10
        }
        r_res = await client.post(f"{ROLES_URL}/", json=role_payload, headers=headers)
        assert r_res.status_code in (200, 201), r_res.text
        role_id = r_res.json()["id"]

        ar_req = {"role_ids": [role_id]}
        ar_res = await client.post(f"{GROUP_URL}/{group_id}/roles", json=ar_req, headers=headers)
        assert ar_res.status_code in (200, 201)
        lr_res = await client.get(f"{GROUP_URL}/{group_id}/roles", headers=headers)
        assert lr_res.status_code == 200 and role_id in set(lr_res.json())
        rr_res = await client.delete(f"{GROUP_URL}/{group_id}/roles/{role_id}", headers=headers)
        assert rr_res.status_code in (200, 204)

        # 7) Soft delete group
        d_res = await client.delete(f"{GROUP_URL}/{group_id}", headers=headers)
        assert d_res.status_code in (200, 204)



@pytest.mark.asyncio
async def test_group_parent_cycle_validation():
    async with httpx.AsyncClient() as client:
        # Auth
        auth = await client.post(AUTH_URL, json=TEST_USER)
        if auth.status_code != 200:
            pytest.skip(f"Auth failed: {auth.status_code}")
        token = auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create two groups A and B
        a_res = await client.post(f"{GROUP_URL}/", json={"name": f"grp_a_{uuid4().hex[:6]}", "display_name": "A"}, headers=headers)
        b_res = await client.post(f"{GROUP_URL}/", json={"name": f"grp_b_{uuid4().hex[:6]}", "display_name": "B"}, headers=headers)
        assert a_res.status_code in (200, 201) and b_res.status_code in (200, 201)
        a_id = a_res.json()["id"]; b_id = b_res.json()["id"]

        # Set A parent to B
        u1 = await client.patch(f"{GROUP_URL}/{a_id}", json={"parent_group_id": b_id}, headers=headers)
        assert u1.status_code == 200
        # Attempt to set B parent to A -> should be 400
        u2 = await client.patch(f"{GROUP_URL}/{b_id}", json={"parent_group_id": a_id}, headers=headers)
        assert u2.status_code == 400


@pytest.mark.asyncio
async def test_group_idempotent_membership_and_roles():
    async with httpx.AsyncClient() as client:
        # Auth
        auth = await client.post(AUTH_URL, json=TEST_USER)
        if auth.status_code != 200:
            pytest.skip(f"Auth failed: {auth.status_code}")
        token = auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create group
        g_res = await client.post(f"{GROUP_URL}/", json={"name": f"grp_{uuid4().hex[:6]}"}, headers=headers)
        assert g_res.status_code in (200, 201)
        gid = g_res.json()["id"]

        # Create user
        user_payload = {
            "email": f"idemp-{uuid4().hex[:6]}@example.com",
            "username": f"idemp_{uuid4().hex[:6]}",
            "password": "TempPass123!",
            "is_active": True
        }
        u_res = await client.post(f"{USERS_URL}/", json=user_payload, headers=headers)
        assert u_res.status_code in (200, 201)
        uid = u_res.json()["id"]

        # Add same user twice
        add1 = await client.post(f"{GROUP_URL}/{gid}/users", json={"user_ids": [uid]}, headers=headers)
        add2 = await client.post(f"{GROUP_URL}/{gid}/users", json={"user_ids": [uid]}, headers=headers)
        assert add1.status_code in (200, 201)
        assert add2.status_code in (200, 201)
        assert add1.json().get("added", 0) >= 1
        assert add2.json().get("added", 0) == 0

        # Create role
        role_payload = {
            "name": f"idemp_role_{uuid4().hex[:6]}",
            "type": "custom",
            "is_assignable": True,
            "priority": 1
        }
        r_res = await client.post(f"{ROLES_URL}/", json=role_payload, headers=headers)
        assert r_res.status_code in (200, 201)
        rid = r_res.json()["id"]

        # Assign same role twice
        as1 = await client.post(f"{GROUP_URL}/{gid}/roles", json={"role_ids": [rid]}, headers=headers)
        as2 = await client.post(f"{GROUP_URL}/{gid}/roles", json={"role_ids": [rid]}, headers=headers)
        assert as1.status_code in (200, 201)
        assert as2.status_code in (200, 201)
        assert as1.json().get("assigned", 0) >= 1
        assert as2.json().get("assigned", 0) == 0


@pytest.mark.asyncio
async def test_group_list_filters_and_search():
    async with httpx.AsyncClient() as client:
        # Auth
        auth = await client.post(AUTH_URL, json=TEST_USER)
        if auth.status_code != 200:
            pytest.skip(f"Auth failed: {auth.status_code}")
        token = auth.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a group with a distinctive name
        name = f"search_{uuid4().hex[:6]}"
        c = await client.post(f"{GROUP_URL}/", json={"name": name, "display_name": "Searchable"}, headers=headers)
        assert c.status_code in (200, 201)

        # Search
        q = name[:6]
        res = await client.get(f"{GROUP_URL}/", params={"search": q, "limit": 5}, headers=headers)
        assert res.status_code == 200
        items = res.json().get("items", [])
        assert any(g["name"] == name for g in items)


@pytest.mark.asyncio
async def test_group_auth_required():
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(f"{GROUP_URL}/")
        except Exception:
            pytest.skip("Server not reachable for auth-required check")
        assert res.status_code == 401

