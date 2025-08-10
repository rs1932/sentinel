"""
Unit tests for RolePermissionService
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.role_permission_service import RolePermissionService
from src.schemas.permission import (
    RolePermissionAssignment, PermissionCreate, PermissionResponse, 
    RolePermissionResponse, RolePermissionsListResponse
)
from src.models.permission import Permission, RolePermission
from src.models.role import Role
from src.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def role_permission_service(mock_db):
    """Create RolePermissionService with mocked database"""
    return RolePermissionService(mock_db)


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_role_id():
    """Sample role ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_permission_id():
    """Sample permission ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def sample_role(sample_role_id, sample_tenant_id):
    """Sample Role model instance"""
    return Role(
        id=sample_role_id,
        tenant_id=sample_tenant_id,
        name="Test Role",
        display_name="Test Role Display",
        type="custom",
        is_active=True
    )


@pytest.fixture
def sample_permission(sample_permission_id, sample_tenant_id):
    """Sample Permission model instance"""
    return Permission(
        id=sample_permission_id,
        tenant_id=sample_tenant_id,
        name="Test Permission",
        resource_type="entity",
        resource_path="test/*",
        actions=["read"],
        conditions={},
        field_permissions={},
        is_active=True
    )


@pytest.fixture
def sample_permission_assignment(sample_permission_id):
    """Sample RolePermissionAssignment for testing"""
    return RolePermissionAssignment(permission_id=sample_permission_id)


@pytest.fixture
def sample_permission_create(sample_tenant_id):
    """Sample PermissionCreate for testing"""
    return PermissionCreate(
        tenant_id=sample_tenant_id,
        name="New Test Permission",
        resource_type="entity",
        resource_path="new/*",
        actions=["read"],
        conditions={},
        field_permissions={},
        is_active=True
    )


class TestRolePermissionService:
    """Test cases for RolePermissionService"""

    @pytest.mark.asyncio
    async def test_assign_permissions_to_role_existing_permission(
        self, role_permission_service, mock_db, sample_role, sample_permission,
        sample_permission_assignment, sample_tenant_id, sample_user_id
    ):
        """Test assigning existing permission to role"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        
        # Setup - mock permission service get_permission
        permission_response = PermissionResponse.model_validate(sample_permission)
        role_permission_service.permission_service.get_permission = AsyncMock(return_value=permission_response)
        
        # Setup - mock no existing assignment
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        
        # Configure mock_db.execute to return different results for different queries
        mock_db.execute = AsyncMock(side_effect=[role_result, existing_result])
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        assignments = [sample_permission_assignment]
        result = await role_permission_service.assign_permissions_to_role(
            sample_role.id, sample_tenant_id, assignments, sample_user_id
        )
        
        # Verify
        assert len(result) == 1
        assert isinstance(result[0], RolePermissionResponse)
        assert result[0].role_id == sample_role.id
        assert result[0].granted_by == sample_user_id
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_permissions_to_role_new_permission(
        self, role_permission_service, mock_db, sample_role, sample_permission_create,
        sample_tenant_id, sample_user_id
    ):
        """Test assigning new permission (created during assignment) to role"""
        # Create assignment with new permission
        new_permission_assignment = RolePermissionAssignment(permission=sample_permission_create)
        
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        
        # Setup - mock permission service create_permission
        created_permission = Permission(**sample_permission_create.model_dump())
        created_permission.id = uuid.uuid4()
        permission_response = PermissionResponse.model_validate(created_permission)
        role_permission_service.permission_service.create_permission = AsyncMock(return_value=permission_response)
        
        # Setup - mock no existing assignment
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = None
        
        mock_db.execute = AsyncMock(side_effect=[role_result, existing_result])
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        assignments = [new_permission_assignment]
        result = await role_permission_service.assign_permissions_to_role(
            sample_role.id, sample_tenant_id, assignments, sample_user_id
        )
        
        # Verify
        assert len(result) == 1
        role_permission_service.permission_service.create_permission.assert_called_once_with(sample_permission_create)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_permissions_to_role_not_found(
        self, role_permission_service, mock_db, sample_permission_assignment,
        sample_tenant_id, sample_user_id
    ):
        """Test assigning permissions to non-existent role"""
        # Setup - role not found
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=role_result)
        
        non_existent_role_id = uuid.uuid4()
        assignments = [sample_permission_assignment]
        
        # Execute & Verify
        with pytest.raises(NotFoundError, match="Role not found"):
            await role_permission_service.assign_permissions_to_role(
                non_existent_role_id, sample_tenant_id, assignments, sample_user_id
            )

    @pytest.mark.asyncio
    async def test_assign_permissions_skip_existing(
        self, role_permission_service, mock_db, sample_role, sample_permission,
        sample_permission_assignment, sample_tenant_id, sample_user_id
    ):
        """Test that existing role-permission assignments are skipped"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        
        # Setup - mock permission service get_permission
        permission_response = PermissionResponse.model_validate(sample_permission)
        role_permission_service.permission_service.get_permission = AsyncMock(return_value=permission_response)
        
        # Setup - mock existing assignment exists
        existing_assignment = RolePermission(role_id=sample_role.id, permission_id=sample_permission.id)
        existing_result = MagicMock()
        existing_result.scalar_one_or_none.return_value = existing_assignment
        
        mock_db.execute = AsyncMock(side_effect=[role_result, existing_result])
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        assignments = [sample_permission_assignment]
        result = await role_permission_service.assign_permissions_to_role(
            sample_role.id, sample_tenant_id, assignments, sample_user_id
        )
        
        # Verify - no new assignment created since it already exists
        assert len(result) == 0
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_role_permissions_success(
        self, role_permission_service, mock_db, sample_role, sample_permission,
        sample_tenant_id
    ):
        """Test getting role permissions successfully"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        
        # Setup - mock direct permissions
        direct_permissions_result = MagicMock()
        direct_permissions_scalars = MagicMock()
        direct_permissions_scalars.all.return_value = [sample_permission]
        direct_permissions_result.scalars.return_value = direct_permissions_scalars
        
        mock_db.execute = AsyncMock(side_effect=[role_result, direct_permissions_result])
        
        # Execute
        result = await role_permission_service.get_role_permissions(
            sample_role.id, sample_tenant_id, include_inherited=False
        )
        
        # Verify
        assert isinstance(result, RolePermissionsListResponse)
        assert len(result.direct_permissions) == 1
        assert result.direct_permissions[0].id == sample_permission.id
        assert len(result.inherited_permissions) == 0
        assert len(result.effective_permissions) == 1

    @pytest.mark.asyncio
    async def test_get_role_permissions_not_found(
        self, role_permission_service, mock_db, sample_tenant_id
    ):
        """Test getting permissions for non-existent role"""
        # Setup - role not found
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=role_result)
        
        non_existent_role_id = uuid.uuid4()
        
        # Execute & Verify
        with pytest.raises(NotFoundError, match="Role not found"):
            await role_permission_service.get_role_permissions(
                non_existent_role_id, sample_tenant_id
            )

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_success(
        self, role_permission_service, mock_db, sample_role, sample_permission_id,
        sample_tenant_id
    ):
        """Test successfully removing permission from role"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        mock_db.execute = AsyncMock(return_value=role_result)
        
        # Setup - mock delete operation
        delete_result = MagicMock()
        delete_result.rowcount = 1
        mock_db.execute = AsyncMock(side_effect=[role_result, delete_result])
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await role_permission_service.remove_permission_from_role(
            sample_role.id, sample_permission_id, sample_tenant_id
        )
        
        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_not_found(
        self, role_permission_service, mock_db, sample_permission_id, sample_tenant_id
    ):
        """Test removing permission from non-existent role"""
        # Setup - role not found
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=role_result)
        
        non_existent_role_id = uuid.uuid4()
        
        # Execute & Verify
        with pytest.raises(NotFoundError, match="Role not found"):
            await role_permission_service.remove_permission_from_role(
                non_existent_role_id, sample_permission_id, sample_tenant_id
            )

    @pytest.mark.asyncio
    async def test_remove_permission_from_role_assignment_not_found(
        self, role_permission_service, mock_db, sample_role, sample_permission_id,
        sample_tenant_id
    ):
        """Test removing non-existent permission assignment"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        
        # Setup - mock delete operation returns 0 rows affected
        delete_result = MagicMock()
        delete_result.rowcount = 0
        
        mock_db.execute = AsyncMock(side_effect=[role_result, delete_result])
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await role_permission_service.remove_permission_from_role(
            sample_role.id, sample_permission_id, sample_tenant_id
        )
        
        # Verify
        assert result is False
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_all_permissions_from_role_success(
        self, role_permission_service, mock_db, sample_role, sample_tenant_id
    ):
        """Test successfully removing all permissions from role"""
        # Setup - mock role exists
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = sample_role
        mock_db.execute = AsyncMock(return_value=role_result)
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await role_permission_service.remove_all_permissions_from_role(
            sample_role.id, sample_tenant_id
        )
        
        # Verify
        assert result is True
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_remove_all_permissions_from_role_not_found(
        self, role_permission_service, mock_db, sample_tenant_id
    ):
        """Test removing all permissions from non-existent role"""
        # Setup - role not found
        role_result = MagicMock()
        role_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=role_result)
        
        non_existent_role_id = uuid.uuid4()
        
        # Execute & Verify
        with pytest.raises(NotFoundError, match="Role not found"):
            await role_permission_service.remove_all_permissions_from_role(
                non_existent_role_id, sample_tenant_id
            )

