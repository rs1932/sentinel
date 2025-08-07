import pytest
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.tenant_service import TenantService
from src.schemas.tenant import TenantCreate, TenantUpdate, TenantQuery, SubTenantCreate
from src.models.tenant import Tenant, TenantType, IsolationMode
from src.utils.exceptions import NotFoundError, ConflictError, ValidationError

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def tenant_service(mock_db):
    return TenantService(mock_db)

@pytest.fixture
def sample_tenant():
    return Tenant(
        id=uuid4(),
        name="Test Tenant",
        code="TEST-001",
        type=TenantType.ROOT,
        isolation_mode=IsolationMode.SHARED,
        is_active=True,
        settings={},
        features=[],
        metadata={}
    )

@pytest.mark.asyncio
async def test_create_tenant_success(tenant_service, mock_db):
    tenant_data = TenantCreate(
        name="New Tenant",
        code="NEW-001",
        type=TenantType.ROOT,
        isolation_mode=IsolationMode.SHARED
    )
    
    mock_db.query().filter().first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    result = await tenant_service.create_tenant(tenant_data)
    
    assert mock_db.add.called
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_create_tenant_duplicate_code(tenant_service, mock_db, sample_tenant):
    tenant_data = TenantCreate(
        name="New Tenant",
        code="TEST-001",
        type=TenantType.ROOT,
        isolation_mode=IsolationMode.SHARED
    )
    
    mock_db.query().filter().first.return_value = sample_tenant
    
    with pytest.raises(ConflictError) as exc_info:
        await tenant_service.create_tenant(tenant_data)
    
    assert "already exists" in str(exc_info.value)

@pytest.mark.asyncio
async def test_get_tenant_success(tenant_service, mock_db, sample_tenant):
    tenant_id = sample_tenant.id
    mock_db.query().filter().first.return_value = sample_tenant
    
    result = await tenant_service.get_tenant(tenant_id)
    
    assert result == sample_tenant

@pytest.mark.asyncio
async def test_get_tenant_not_found(tenant_service, mock_db):
    tenant_id = uuid4()
    mock_db.query().filter().first.return_value = None
    
    with pytest.raises(NotFoundError) as exc_info:
        await tenant_service.get_tenant(tenant_id)
    
    assert "not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_tenant_success(tenant_service, mock_db, sample_tenant):
    tenant_id = sample_tenant.id
    update_data = TenantUpdate(name="Updated Tenant")
    
    mock_db.query().filter().first.return_value = sample_tenant
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    result = await tenant_service.update_tenant(tenant_id, update_data)
    
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_update_platform_tenant(tenant_service, mock_db):
    platform_tenant = Tenant(
        id=uuid4(),
        name="Sentinel Platform",
        code="PLATFORM",
        type=TenantType.ROOT,
        isolation_mode=IsolationMode.DEDICATED,
        is_active=True
    )
    
    mock_db.query().filter().first.return_value = platform_tenant
    update_data = TenantUpdate(name="Changed Name")
    
    with pytest.raises(ValidationError) as exc_info:
        await tenant_service.update_tenant(platform_tenant.id, update_data)
    
    assert "Platform tenant cannot be modified" in str(exc_info.value)

@pytest.mark.asyncio
async def test_delete_tenant_success(tenant_service, mock_db, sample_tenant):
    tenant_id = sample_tenant.id
    
    mock_db.query().filter().first.return_value = sample_tenant
    mock_db.query().filter().count.return_value = 0
    mock_db.delete = MagicMock()
    mock_db.commit = MagicMock()
    
    result = await tenant_service.delete_tenant(tenant_id)
    
    assert result is True
    assert mock_db.delete.called
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_delete_tenant_with_sub_tenants(tenant_service, mock_db, sample_tenant):
    tenant_id = sample_tenant.id
    
    mock_db.query().filter().first.return_value = sample_tenant
    mock_db.query().filter().count.return_value = 2
    
    with pytest.raises(ValidationError) as exc_info:
        await tenant_service.delete_tenant(tenant_id)
    
    assert "Cannot delete tenant with" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_sub_tenant_success(tenant_service, mock_db, sample_tenant):
    parent_id = sample_tenant.id
    sub_tenant_data = SubTenantCreate(
        name="Sub Tenant",
        code="SUB-001",
        isolation_mode=IsolationMode.SHARED
    )
    
    # Mock the get_tenant method instead of individual db queries
    with patch.object(tenant_service, 'get_tenant', return_value=sample_tenant):
        with patch.object(tenant_service, 'create_tenant') as mock_create:
            mock_sub_tenant = Tenant(
                id=uuid4(),
                name=sub_tenant_data.name,
                code=sub_tenant_data.code,
                type=TenantType.SUB_TENANT,
                isolation_mode=sub_tenant_data.isolation_mode,
                parent_tenant_id=parent_id
            )
            mock_create.return_value = mock_sub_tenant
            
            result = await tenant_service.create_sub_tenant(parent_id, sub_tenant_data)
            
            # Verify create_tenant was called with correct data
            mock_create.assert_called_once()
            call_args = mock_create.call_args[0][0]
            assert call_args.type == TenantType.SUB_TENANT
            assert call_args.parent_tenant_id == parent_id
            assert result == mock_sub_tenant

@pytest.mark.asyncio
async def test_activate_tenant_success(tenant_service, mock_db):
    tenant = Tenant(
        id=uuid4(),
        name="Test Tenant",
        code="TEST-001",
        type=TenantType.ROOT,
        isolation_mode=IsolationMode.SHARED,
        is_active=False
    )
    
    mock_db.query().filter().first.return_value = tenant
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    result = await tenant_service.activate_tenant(tenant.id)
    
    assert tenant.is_active is True
    assert mock_db.commit.called

@pytest.mark.asyncio
async def test_deactivate_tenant_success(tenant_service, mock_db, sample_tenant):
    mock_db.query().filter().first.return_value = sample_tenant
    mock_db.query().filter().count.return_value = 0
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    
    result = await tenant_service.deactivate_tenant(sample_tenant.id)
    
    assert sample_tenant.is_active is False
    assert mock_db.commit.called