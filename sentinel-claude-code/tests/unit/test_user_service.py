"""
Unit tests for User Service (Module 3)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.user_service import UserService
from src.models.user import User
from src.models.tenant import Tenant
from src.schemas.user import (
    UserCreate, UserUpdate, UserQuery, BulkOperationType, 
    UserBulkOperation, PasswordChange, SortField, SortOrder
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError, AuthenticationError


class TestUserService:
    """Test cases for UserService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def user_service(self, mock_db):
        """UserService instance with mocked database"""
        return UserService(mock_db)
    
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
    def sample_user(self, sample_tenant):
        """Sample user for testing"""
        return User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email="test@example.com",
            username="testuser",
            password_hash="hashed_password",
            is_service_account=False,
            is_active=True,
            attributes={"department": "engineering"},
            preferences={"theme": "dark"},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_service, mock_db, sample_tenant):
        """Test successful user creation"""
        # Mock database responses
        tenant_result = Mock()
        tenant_result.scalar_one_or_none.return_value = sample_tenant
        mock_db.execute.return_value = tenant_result
        
        # Setup user data
        user_data = UserCreate(
            email="newuser@example.com",
            username="newuser",
            password="password123",
            attributes={"department": "sales"},
            is_active=True
        )
        
        # Mock no existing user
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [tenant_result, user_result, user_result]  # tenant, email check, username check
        
        # Mock password manager
        user_service.password_manager.hash_password.return_value = "hashed_password123"
        
        # Create mock user for return
        created_user = User(
            id=uuid.uuid4(),
            tenant_id=sample_tenant.id,
            email=user_data.email.lower(),
            username=user_data.username,
            password_hash="hashed_password123",
            is_service_account=False,
            is_active=True,
            attributes=user_data.attributes,
            preferences={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_db.refresh = AsyncMock()
        mock_db.refresh.side_effect = lambda user: setattr(user, 'id', created_user.id)
        
        # Execute
        result = await user_service.create_user(user_data, tenant_id=sample_tenant.id)
        
        # Verify
        assert result.email == user_data.email.lower()
        assert result.username == user_data.username
        assert result.is_active == user_data.is_active
        assert result.attributes == user_data.attributes
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, mock_db, sample_tenant, sample_user):
        """Test user creation with duplicate email"""
        # Mock database responses
        tenant_result = Mock()
        tenant_result.scalar_one_or_none.return_value = sample_tenant
        
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user  # Existing user
        
        mock_db.execute.side_effect = [tenant_result, user_result]
        
        user_data = UserCreate(
            email=sample_user.email,  # Same email as existing user
            username="differentuser",
            password="password123"
        )
        
        # Execute and verify
        with pytest.raises(ConflictError) as exc_info:
            await user_service.create_user(user_data, tenant_id=sample_tenant.id)
        
        assert "already exists" in str(exc_info.value)
        mock_db.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_user_success(self, user_service, mock_db, sample_user):
        """Test successful user retrieval"""
        # Mock database response
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Execute
        result = await user_service.get_user(sample_user.id, tenant_id=sample_user.tenant_id)
        
        # Verify
        assert result.id == sample_user.id
        assert result.email == sample_user.email
        assert result.username == sample_user.username
    
    @pytest.mark.asyncio
    async def test_get_user_not_found(self, user_service, mock_db):
        """Test user retrieval when user doesn't exist"""
        # Mock database response
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = user_result
        
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        
        # Execute and verify
        with pytest.raises(NotFoundError):
            await user_service.get_user(user_id, tenant_id=tenant_id)
    
    @pytest.mark.asyncio
    async def test_list_users_success(self, user_service, mock_db, sample_user):
        """Test successful user listing"""
        # Mock count query
        count_result = Mock()
        count_result.scalar.return_value = 1
        
        # Mock user query
        user_result = Mock()
        user_result.scalars.return_value.all.return_value = [sample_user]
        
        mock_db.execute.side_effect = [count_result, user_result]
        
        query_params = UserQuery(
            page=1,
            limit=50,
            sort=SortField.created_at,
            order=SortOrder.desc
        )
        
        # Execute
        result = await user_service.list_users(query_params, tenant_id=sample_user.tenant_id)
        
        # Verify
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == sample_user.id
        assert result.page == 1
        assert result.limit == 50
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, user_service, mock_db, sample_user):
        """Test successful user update"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.side_effect = [user_result, None]  # user lookup, then update
        
        update_data = UserUpdate(
            username="updateduser",
            attributes={"department": "marketing"},
            is_active=False
        )
        
        # Execute
        result = await user_service.update_user(
            sample_user.id, 
            update_data, 
            tenant_id=sample_user.tenant_id
        )
        
        # Verify
        assert mock_db.execute.call_count == 2  # lookup + update
        assert mock_db.commit.called
        assert mock_db.refresh.called
    
    @pytest.mark.asyncio
    async def test_delete_user_soft_delete(self, user_service, mock_db, sample_user):
        """Test soft delete user"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.side_effect = [user_result, None]  # lookup, then update
        
        # Execute
        await user_service.delete_user(
            sample_user.id, 
            tenant_id=sample_user.tenant_id,
            soft_delete=True
        )
        
        # Verify
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, user_service, mock_db, sample_user):
        """Test successful password change"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.side_effect = [user_result, None]  # lookup, then update
        
        # Mock password verification and hashing
        user_service.password_manager.verify_password.return_value = True
        user_service.password_manager.hash_password.return_value = "new_hashed_password"
        
        password_data = PasswordChange(
            current_password="oldpassword",
            new_password="newpassword123"
        )
        
        # Execute
        await user_service.change_password(
            sample_user.id,
            password_data,
            tenant_id=sample_user.tenant_id
        )
        
        # Verify
        user_service.password_manager.verify_password.assert_called_once()
        user_service.password_manager.hash_password.assert_called_once()
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, user_service, mock_db, sample_user):
        """Test password change with wrong current password"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Mock password verification failure
        user_service.password_manager.verify_password.return_value = False
        
        password_data = PasswordChange(
            current_password="wrongpassword",
            new_password="newpassword123"
        )
        
        # Execute and verify
        with pytest.raises(AuthenticationError):
            await user_service.change_password(
                sample_user.id,
                password_data,
                tenant_id=sample_user.tenant_id
            )
    
    @pytest.mark.asyncio
    async def test_lock_user_success(self, user_service, mock_db, sample_user):
        """Test successful user locking"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.side_effect = [user_result, None]  # lookup, then update
        
        # Execute
        await user_service.lock_user(
            sample_user.id,
            duration_minutes=60,
            tenant_id=sample_user.tenant_id
        )
        
        # Verify
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_unlock_user_success(self, user_service, mock_db, sample_user):
        """Test successful user unlocking"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.side_effect = [user_result, None]  # lookup, then update
        
        # Execute
        await user_service.unlock_user(
            sample_user.id,
            tenant_id=sample_user.tenant_id
        )
        
        # Verify
        assert mock_db.execute.call_count == 2
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_bulk_operation_activate(self, user_service, mock_db):
        """Test bulk activate operation"""
        user_ids = [uuid.uuid4(), uuid.uuid4()]
        tenant_id = uuid.uuid4()
        
        bulk_data = UserBulkOperation(
            operation=BulkOperationType.activate,
            user_ids=user_ids
        )
        
        # Execute
        result = await user_service.bulk_operation(
            bulk_data,
            tenant_id=tenant_id
        )
        
        # Verify
        assert result.total_requested == 2
        assert result.successful == 2
        assert result.failed == 0
        assert mock_db.commit.called
    
    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_db, sample_user):
        """Test get user by email"""
        # Mock database response
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Execute
        result = await user_service.get_user_by_email(
            sample_user.email,
            tenant_id=sample_user.tenant_id
        )
        
        # Verify
        assert result is not None
        assert result.email == sample_user.email
    
    @pytest.mark.asyncio
    async def test_get_user_permissions_placeholder(self, user_service, mock_db, sample_user):
        """Test get user permissions (placeholder implementation)"""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = user_result
        
        # Execute
        result = await user_service.get_user_permissions(
            sample_user.id,
            tenant_id=sample_user.tenant_id
        )
        
        # Verify placeholder response
        assert result.user_id == sample_user.id
        assert result.tenant_id == sample_user.tenant_id
        assert result.direct_permissions == []
        assert result.inherited_permissions == []
        assert result.effective_permissions == []