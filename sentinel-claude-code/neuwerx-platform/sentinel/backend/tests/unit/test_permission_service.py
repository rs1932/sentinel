import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.permission_service import PermissionService
from src.models.permission import Permission
from src.schemas.permission import PermissionCreate, PermissionUpdate


@pytest.fixture
def mock_db():
    return AsyncMock(spec=AsyncSession)


@pytest.mark.asyncio
async def test_create_and_get_permission(mock_db):
    service = PermissionService(mock_db)
    tenant_id = uuid4()

    data = PermissionCreate(
        tenant_id=tenant_id,
        name="View vessels in APAC",
        resource_type="entity",
        resource_id=None,
        resource_path="vessel/*",
        actions=["read"],
        conditions={"attributes.region": "APAC"},
        field_permissions={"vessel_name": ["read"]},
        is_active=True,
    )

    # create_permission uses add/commit/refresh
    def _refresh_set_id(obj):
        # simulate DB assigning an id on insert
        if getattr(obj, "id", None) is None:
            obj.id = uuid4()
    mock_db.refresh.side_effect = _refresh_set_id
    created = await service.create_permission(data)
    assert created.name == data.name
    assert created.tenant_id == tenant_id

    # get_permission uses execute + scalar_one_or_none
    perm_obj = Permission(
        tenant_id=tenant_id,
        name=data.name,
        resource_type=data.resource_type,
        resource_id=None,
        resource_path=data.resource_path,
        actions=data.actions,
        conditions=data.conditions,
        field_permissions=data.field_permissions,
        is_active=True,
    )
    perm_obj.id = created.id
    execute_result = Mock()
    execute_result.scalar_one_or_none.return_value = perm_obj
    mock_db.execute.return_value = execute_result

    fetched = await service.get_permission(created.id, tenant_id)
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_update_permission(mock_db):
    service = PermissionService(mock_db)
    tenant_id = uuid4()

    # Mock existing permission
    perm_obj = Permission(
        tenant_id=tenant_id,
        name="Update vessels",
        resource_type="entity",
        resource_id=None,
        resource_path="vessel/*",
        actions=["read"],
        conditions={},
        field_permissions={},
        is_active=True,
    )
    perm_obj.id = uuid4()
    res_lookup_1 = Mock()
    res_lookup_1.scalar_one_or_none.return_value = perm_obj

    # After update, return modified object
    perm_updated = Permission(
        tenant_id=tenant_id,
        name="Update vessels",
        resource_type="entity",
        resource_id=None,
        resource_path="vessel/*",
        actions=["read","update"],
        conditions={},
        field_permissions={},
        is_active=True,
    )
    perm_updated.id = perm_obj.id
    res_lookup_2 = Mock()
    res_lookup_2.scalar_one_or_none.return_value = perm_updated

    mock_db.execute.side_effect = [res_lookup_1, None, res_lookup_2]

    updated = await service.update_permission(perm_obj.id, tenant_id, PermissionUpdate(actions=["read","update"]))
    assert set(updated.actions) == {"read","update"}


@pytest.mark.asyncio
async def test_delete_permission(mock_db):
    service = PermissionService(mock_db)
    tenant_id = uuid4()

    # Mock existing permission for delete
    perm_obj = Permission(
        tenant_id=tenant_id,
        name="Temp perm",
        resource_type="entity",
        resource_id=None,
        resource_path="vessel/*",
        actions=["read"],
        conditions={},
        field_permissions={},
        is_active=True,
    )
    perm_obj.id = uuid4()
    res_lookup = Mock()
    res_lookup.scalar_one_or_none.return_value = perm_obj
    mock_db.execute.side_effect = [res_lookup, None, None]

    ok = await service.delete_permission(perm_obj.id, tenant_id)
    assert ok is True


@pytest.mark.asyncio
async def test_create_permission_requires_resource_spec(mock_db):
    service = PermissionService(mock_db)
    tenant_id = uuid4()

    with pytest.raises(Exception):
        await service.create_permission(
            PermissionCreate(
                tenant_id=tenant_id,
                name="Invalid",
                resource_type="entity",
                resource_id=None,
                resource_path=None,
                actions=["read"],
                conditions={},
                field_permissions={},
                is_active=True,
            )
        )

