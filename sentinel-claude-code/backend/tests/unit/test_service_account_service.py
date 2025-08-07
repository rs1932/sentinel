"""
Unit tests for Service Account Service (Module 3)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from src.services.service_account_service import ServiceAccountService
from src.models.user import User
from src.models.tenant import Tenant
from src.schemas.user import (
    ServiceAccountCreate, ServiceAccountUpdate, UserQuery, 
    CredentialRotation, SortField, SortOrder
)
from src.core.exceptions import NotFoundError, ConflictError


class TestServiceAccountService:
    """Test cases for ServiceAccountService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def service_account_service(self, mock_db):
        """ServiceAccountService instance with mocked database"""
        return ServiceAccountService(mock_db)
    
    @pytest.fixture
    def sample_tenant(self):
        """Sample tenant for testing"""
        return Tenant(
            id=uuid.uuid4(),
            name="Test Tenant",
            code="TEST",
            is_active=True
        )
    
    @pytest.fixture
    def sample_service_account(self, sample_tenant):
        """Sample service account for testing"""
        return User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="svc_test@test.service",
            username="Test Service Account",
            password_hash=None,  # Service accounts don't use passwords
            is_service_account=True,
            service_account_key="test_client_secret_12345",
            is_active=True,
            attributes={"service_type": "integration"},
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_create_service_account_success(self, service_account_service, mock_db, sample_tenant):
        """Test successful service account creation"""
        # Mock database responses
        tenant_result = Mock()
        tenant_result.scalar_one_or_none.return_value = sample_tenant
        
        # Mock no existing service account
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [tenant_result, sa_result]
        
        account_data = ServiceAccountCreate(
            name="Test Integration Service",
            description="Service for testing integration",
            attributes={"service_type": "integration"},
            is_active=True
        )
        
        # Create mock service account for return
        created_sa = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email=f"svc_test_integration_service_abcd@{sample_tenant.code.lower()}.service",
            username=account_data.name,
            password_hash=None,
            is_service_account=True,
            service_account_key="generated_secret_12345",
            is_active=True,
            attributes=account_data.attributes,
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_db.refresh = AsyncMock()
        mock_db.refresh.side_effect = lambda user: setattr(user, 'id', created_sa.id)
        
        # Execute
        account_response, credential_response = await service_account_service.create_service_account(
            account_data, tenant_id=sample_tenant.id
        )
        
        # Verify account response
        assert account_response.name == account_data.name
        assert account_response.is_active == account_data.is_active
        assert account_response.attributes == account_data.attributes
        assert account_response.client_id.startswith("svc_")
        
        # Verify credential response
        assert credential_response.client_id.startswith("svc_")
        assert len(credential_response.client_secret) > 20  # Should be a long secret
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_service_account_duplicate_name(self, service_account_service, mock_db, sample_tenant, sample_service_account):
        """Test service account creation with duplicate name"""
        # Mock database responses
        tenant_result = Mock()
        tenant_result.scalar_one_or_none.return_value = sample_tenant
        
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account  # Existing SA
        
        mock_db.execute.side_effect = [tenant_result, sa_result]
        
        account_data = ServiceAccountCreate(
            name=sample_service_account.username,  # Same name as existing SA
            description="Duplicate service account"
        )
        
        # Execute and verify
        with pytest.raises(ConflictError) as exc_info:
            await service_account_service.create_service_account(
                account_data, tenant_id=sample_tenant.id
            )
        
        assert "already exists" in str(exc_info.value)
        mock_db.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_service_account_success(self, service_account_service, mock_db, sample_service_account):
        """Test successful service account retrieval"""
        # Mock database response
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account
        mock_db.execute.return_value = sa_result
        
        # Execute
        result = await service_account_service.get_service_account(
            sample_service_account.id, 
            tenant_id=sample_service_account.tenant_id
        )
        
        # Verify
        assert result.id == sample_service_account.id
        assert result.name == sample_service_account.username
        assert result.is_active == sample_service_account.is_active
        assert result.client_id.startswith("svc_")
    
    @pytest.mark.asyncio
    async def test_get_service_account_not_found(self, service_account_service, mock_db):
        """Test service account retrieval when account doesn't exist"""
        # Mock database response
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = sa_result
        
        account_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        
        # Execute and verify
        with pytest.raises(NotFoundError):
            await service_account_service.get_service_account(account_id, tenant_id=tenant_id)
    
    @pytest.mark.asyncio
    async def test_list_service_accounts_success(self, service_account_service, mock_db, sample_service_account):
        """Test successful service account listing"""
        # Mock count query
        count_result = Mock()
        count_result.scalar.return_value = 1
        
        # Mock service account query
        sa_result = Mock()
        sa_result.scalars.return_value.all.return_value = [sample_service_account]
        
        mock_db.execute.side_effect = [count_result, sa_result]
        
        query_params = UserQuery(
            page=1,
            limit=50,
            sort=SortField.created_at,
            order=SortOrder.desc
        )
        
        # Execute
        result = await service_account_service.list_service_accounts(
            query_params, 
            tenant_id=sample_service_account.tenant_id
        )
        
        # Verify
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == sample_service_account.id
        assert result.items[0].client_id.startswith("svc_")
        assert result.page == 1
        assert result.limit == 50
    
    @pytest.mark.asyncio
    async def test_update_service_account_success(self, service_account_service, mock_db, sample_service_account):
        """Test successful service account update"""
        # Mock service account lookup
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account
        mock_db.execute.side_effect = [sa_result, None]  # lookup, then update
        
        update_data = ServiceAccountUpdate(
            name="Updated Service Account",
            description="Updated description",
            attributes={"service_type": "api_integration"},
            is_active=False
        )
        
        # Execute
        result = await service_account_service.update_service_account(
            sample_service_account.id,
            update_data,
            tenant_id=sample_service_account.tenant_id
        )
        
        # Verify
        assert mock_db.execute.call_count == 2  # lookup + update
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_delete_service_account_soft_delete(self, service_account_service, mock_db, sample_service_account):
        """Test soft delete service account"""
        # Mock service account lookup
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account
        mock_db.execute.side_effect = [sa_result, None]  # lookup, then update
        
        # Execute
        await service_account_service.delete_service_account(
            sample_service_account.id,
            tenant_id=sample_service_account.tenant_id,
            soft_delete=True
        )
        
        # Verify
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_rotate_credentials_success(self, service_account_service, mock_db, sample_service_account):
        """Test successful credential rotation"""
        # Mock service account lookup
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account
        mock_db.execute.side_effect = [sa_result, None]  # lookup, then update
        
        rotation_data = CredentialRotation(revoke_existing=True)
        
        # Execute
        result = await service_account_service.rotate_credentials(
            sample_service_account.id,
            rotation_data,
            tenant_id=sample_service_account.tenant_id
        )
        
        # Verify
        assert result.client_id.startswith("svc_")
        assert len(result.client_secret) > 20  # Should be a new long secret
        assert result.client_secret != sample_service_account.service_account_key  # Should be different
        assert mock_db.execute.call_count == 2  # lookup + update
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, service_account_service, mock_db, sample_service_account):
        """Test successful API key validation"""
        # Mock service account lookup
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = sample_service_account
        mock_db.execute.return_value = sa_result
        
        client_id = service_account_service._generate_client_id_from_account(sample_service_account)
        client_secret = sample_service_account.service_account_key
        
        # Execute
        result = await service_account_service.validate_api_key(
            client_id,
            client_secret,
            tenant_id=sample_service_account.tenant_id
        )
        
        # Verify
        assert result is not None
        assert result.id == sample_service_account.id
        assert result.is_service_account == True
    
    @pytest.mark.asyncio
    async def test_validate_api_key_invalid(self, service_account_service, mock_db):
        """Test API key validation with invalid credentials"""
        # Mock service account lookup - not found
        sa_result = Mock()
        sa_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = sa_result
        
        client_id = "svc_invalid_client"
        client_secret = "invalid_secret"
        tenant_id = uuid.uuid4()
        
        # Execute
        result = await service_account_service.validate_api_key(
            client_id,
            client_secret,
            tenant_id=tenant_id
        )
        
        # Verify
        assert result is None
    
    def test_generate_client_id_from_account(self, service_account_service, sample_service_account):
        """Test client ID generation from service account"""
        client_id = service_account_service._generate_client_id_from_account(sample_service_account)
        
        # Verify format
        assert client_id.startswith("svc_")
        assert len(client_id) > 10
        assert "_" in client_id  # Should have underscores for name formatting
    
    def test_generate_client_id_no_username(self, service_account_service, sample_tenant):
        """Test client ID generation when service account has no username"""
        sa_no_username = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="svc_nousername@test.service",
            username=None,  # No username
            is_service_account=True,
            service_account_key="test_secret"
        )
        
        client_id = service_account_service._generate_client_id_from_account(sa_no_username)
        
        # Verify format - should use account ID when no username
        assert client_id.startswith("svc_")
        assert str(sa_no_username.id).replace('-', '')[:8] in client_id