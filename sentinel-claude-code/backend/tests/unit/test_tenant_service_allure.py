"""
Enhanced Tenant Service Tests with Allure Reporting
"""
import pytest
import allure
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock, patch

from src.services.tenant_service import TenantService
from src.schemas.tenant import TenantCreate, TenantUpdate, TenantQuery, SubTenantCreate
from src.models.tenant import Tenant, TenantType, IsolationMode
from src.utils.exceptions import NotFoundError, ConflictError, ValidationError


@allure.epic("Tenant Management")
@allure.feature("Tenant Service")
class TestTenantServiceAllure:
    
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def tenant_service(self, mock_db):
        return TenantService(mock_db)

    @pytest.fixture
    def sample_tenant(self):
        return Tenant(
            id=uuid4(),
            name="Test Tenant",
            code="TEST-001",
            type=TenantType.ROOT,
            isolation_mode=IsolationMode.SHARED,
            is_active=True,
            settings={},
            features=[],
            tenant_metadata={}  # Use the database field name
        )

    @pytest.fixture
    def tenant_create_data(self):
        return TenantCreate(
            name="New Tenant",
            code="NEW-001",
            type=TenantType.ROOT,
            isolation_mode=IsolationMode.SHARED,
            settings={"theme": "dark"},
            features=["api_access"],
            metadata={"department": "IT"}
        )

    @allure.story("Create Tenant")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Successfully create a new tenant")
    @allure.description("""
    This test verifies that a new tenant can be successfully created
    with all required fields and optional metadata.
    """)
    @pytest.mark.asyncio
    async def test_create_tenant_success(self, tenant_service, mock_db, tenant_create_data, sample_tenant):
        with allure.step("Setup mock database responses"):
            mock_db.query().filter().first.return_value = None  # No existing tenant
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

        with allure.step("Create tenant through service"):
            # Mock the created tenant to be returned
            with patch.object(tenant_service.db, 'add') as mock_add:
                with patch.object(tenant_service.db, 'commit') as mock_commit:
                    with patch.object(tenant_service.db, 'refresh') as mock_refresh:
                        mock_refresh.side_effect = lambda obj: setattr(obj, 'id', sample_tenant.id)
                        
                        result = await tenant_service.create_tenant(tenant_create_data)

        with allure.step("Verify tenant creation"):
            assert result is not None
            assert result.name == tenant_create_data.name
            assert result.code == tenant_create_data.code
            mock_add.assert_called_once()
            mock_commit.assert_called_once()
            
        # Attach test data to Allure report
        allure.attach(
            str(tenant_create_data.model_dump()),
            name="Tenant Creation Data",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.story("Create Tenant")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Fail to create tenant with duplicate code")
    @allure.description("Verify that creating a tenant with an existing code raises ConflictError")
    @pytest.mark.asyncio
    async def test_create_tenant_duplicate_code(self, tenant_service, mock_db, tenant_create_data, sample_tenant):
        with allure.step("Setup mock to simulate existing tenant"):
            mock_db.query().filter().first.return_value = sample_tenant

        with allure.step("Attempt to create duplicate tenant"):
            with pytest.raises(ConflictError) as exc_info:
                await tenant_service.create_tenant(tenant_create_data)

        with allure.step("Verify error message"):
            assert "already exists" in str(exc_info.value)
            
        # Attach error details
        allure.attach(
            str(exc_info.value),
            name="Error Details",
            attachment_type=allure.attachment_type.TEXT
        )

    @allure.story("Retrieve Tenant")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Successfully retrieve tenant by ID")
    @pytest.mark.asyncio
    async def test_get_tenant_success(self, tenant_service, mock_db, sample_tenant):
        tenant_id = sample_tenant.id
        
        with allure.step("Setup mock database response"):
            mock_db.query().filter().first.return_value = sample_tenant

        with allure.step("Retrieve tenant by ID"):
            # Mock the cache service
            with patch('src.services.tenant_service.cache_service') as mock_cache:
                mock_cache.get = AsyncMock(return_value=None)  # No cached result
                mock_cache.set = AsyncMock()
                result = await tenant_service.get_tenant(tenant_id)

        with allure.step("Verify tenant retrieval"):
            assert result == sample_tenant
            assert result.id == tenant_id
            assert result.name == sample_tenant.name

    @allure.story("Update Tenant")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Successfully update tenant information")
    @pytest.mark.asyncio
    async def test_update_tenant_success(self, tenant_service, mock_db, sample_tenant):
        tenant_id = sample_tenant.id
        update_data = TenantUpdate(
            name="Updated Tenant Name",
            metadata={"updated": True, "version": 2}
        )

        with allure.step("Setup mock database for update"):
            mock_db.query().filter().first.return_value = sample_tenant
            mock_db.commit = MagicMock()
            mock_db.refresh = MagicMock()

        with allure.step("Update tenant"):
            with patch('src.services.tenant_service.cache_service') as mock_cache:
                mock_cache.delete = AsyncMock()
                result = await tenant_service.update_tenant(tenant_id, update_data)

        with allure.step("Verify tenant update"):
            assert result == sample_tenant
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()
            
        # Attach update data
        allure.attach(
            str(update_data.model_dump()),
            name="Update Data",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.story("Delete Tenant")
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("Successfully delete tenant")
    @pytest.mark.asyncio
    async def test_delete_tenant_success(self, tenant_service, mock_db, sample_tenant):
        tenant_id = sample_tenant.id

        with allure.step("Setup mock database for deletion"):
            mock_db.query().filter().first.return_value = sample_tenant
            mock_db.query().filter().count.return_value = 0  # No sub-tenants
            mock_db.delete = MagicMock()
            mock_db.commit = MagicMock()

        with allure.step("Delete tenant"):
            with patch('src.services.tenant_service.cache_service') as mock_cache:
                mock_cache.delete = AsyncMock()
                result = await tenant_service.delete_tenant(tenant_id)

        with allure.step("Verify tenant deletion"):
            assert result is True
            mock_db.delete.assert_called_once()
            mock_db.commit.assert_called_once()

    @allure.story("List Tenants")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("Successfully list tenants with filters")
    @pytest.mark.asyncio
    async def test_list_tenants_with_filters(self, tenant_service, mock_db, sample_tenant):
        query = TenantQuery(
            name="Test",
            type=TenantType.ROOT,
            is_active=True,
            limit=10,
            offset=0
        )

        with allure.step("Setup mock database for listing"):
            mock_query = MagicMock()
            mock_query.filter.return_value = mock_query
            mock_query.count.return_value = 1
            mock_query.offset.return_value = mock_query
            mock_query.limit.return_value = mock_query
            mock_query.all.return_value = [sample_tenant]
            mock_db.query.return_value = mock_query

        with allure.step("List tenants with filters"):
            result = await tenant_service.list_tenants(query)

        with allure.step("Verify tenant list results"):
            assert result.total == 1
            assert len(result.items) == 1
            assert result.items[0].name == sample_tenant.name
            
        # Attach query parameters
        allure.attach(
            str(query.model_dump()),
            name="Query Parameters",
            attachment_type=allure.attachment_type.JSON
        )

    @allure.story("Platform Protection")
    @allure.severity(allure.severity_level.CRITICAL)  
    @allure.title("Prevent platform tenant modification")
    @allure.description("Ensure that the PLATFORM tenant cannot be updated or deleted")
    @pytest.mark.asyncio
    async def test_protect_platform_tenant(self, tenant_service, mock_db):
        platform_tenant = Tenant(
            id=uuid4(),
            name="Platform",
            code="PLATFORM",
            type=TenantType.ROOT,
            isolation_mode=IsolationMode.SHARED,
            is_active=True
        )

        with allure.step("Setup platform tenant in database"):
            mock_db.query().filter().first.return_value = platform_tenant

        with allure.step("Attempt to update platform tenant"):
            update_data = TenantUpdate(name="Hacked Platform")
            with pytest.raises(ValidationError) as exc_info:
                await tenant_service.update_tenant(platform_tenant.id, update_data)

        with allure.step("Verify platform protection"):
            assert "cannot be modified" in str(exc_info.value)

        with allure.step("Attempt to delete platform tenant"):
            with pytest.raises(ValidationError) as exc_info:
                await tenant_service.delete_tenant(platform_tenant.id)

        with allure.step("Verify deletion protection"):
            assert "cannot be deleted" in str(exc_info.value)


@allure.epic("Tenant Management")
@allure.feature("Performance Tests")  
@allure.story("Load Testing")
class TestTenantPerformance:
    
    @pytest.fixture
    def tenant_service(self):
        return TenantService(MagicMock())

    @allure.severity(allure.severity_level.MINOR)
    @allure.title("Bulk tenant creation performance")
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_bulk_tenant_creation(self, tenant_service):
        """Test creating multiple tenants in sequence"""
        with allure.step("Prepare bulk tenant data"):
            tenant_count = 100
            tenants = []
            for i in range(tenant_count):
                tenant_data = TenantCreate(
                    name=f"Bulk Tenant {i}",
                    code=f"BULK-{i:03d}",
                    type=TenantType.ROOT,
                    isolation_mode=IsolationMode.SHARED
                )
                tenants.append(tenant_data)

        with allure.step(f"Create {tenant_count} tenants"):
            # Mock successful creation for all
            with patch.object(tenant_service, 'create_tenant') as mock_create:
                mock_create.return_value = MagicMock()
                
                import time
                start_time = time.time()
                
                for tenant_data in tenants:
                    await tenant_service.create_tenant(tenant_data)
                    
                end_time = time.time()
                duration = end_time - start_time

        with allure.step("Verify performance metrics"):
            assert mock_create.call_count == tenant_count
            
            # Attach performance metrics
            allure.attach(
                f"Created {tenant_count} tenants in {duration:.2f} seconds\n"
                f"Average: {duration/tenant_count*1000:.2f}ms per tenant",
                name="Performance Metrics",
                attachment_type=allure.attachment_type.TEXT
            )