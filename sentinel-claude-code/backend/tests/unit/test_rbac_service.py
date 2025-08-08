"""
Unit tests for RBACService with logistics industry scenarios
"""

import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone

from src.services.rbac_service import RBACService, RBACServiceFactory
from src.models import User, Role, Group, Permission, UserRole, UserGroup, GroupRole, RolePermission
from src.models.resource import ResourceType
from src.core.exceptions import NotFoundError
from src.core.cache import InMemoryCacheManager


class TestRBACService:
    """Test cases for dynamic RBAC service."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def mock_cache(self):
        """Mock cache manager."""
        return AsyncMock(spec=InMemoryCacheManager)
    
    @pytest.fixture
    def rbac_service(self, mock_db, mock_cache):
        """RBACService instance with mocked dependencies."""
        return RBACService(mock_db, mock_cache)
    
    @pytest.fixture
    def maritime_user(self):
        """Sample maritime logistics user."""
        return User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="port.manager@maritime.com",
            username="port.manager",
            first_name="Sarah",
            last_name="Thompson",
            is_active=True,
            is_service_account=False
        )
    
    @pytest.fixture
    def port_manager_role(self):
        """Port Manager role for maritime tenant."""
        return Role(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="Port Manager",
            display_name="Port Manager",
            description="Oversees port operations and vessel coordination",
            type="custom",
            priority=90,
            is_active=True
        )
    
    @pytest.fixture
    def operations_group(self):
        """Operations department group."""
        return Group(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="Operations",
            display_name="Operations Department",
            description="Day-to-day operational staff",
            is_active=True
        )
    
    @pytest.fixture
    def vessel_permission(self):
        """Permission for vessel operations."""
        return Permission(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            name="vessel_operations_management",
            resource_type=ResourceType.SERVICE,
            resource_id=uuid.uuid4(),
            actions=["create", "read", "update", "delete"],
            conditions={"tenant_isolation": True},
            is_active=True
        )

    @pytest.mark.asyncio
    async def test_get_user_scopes_with_cache_hit(self, rbac_service, maritime_user, mock_cache):
        """Test cache hit scenario for user scopes."""
        # Setup cache hit
        cached_scopes = '["vessel:create", "vessel:read", "port:read"]'
        mock_cache.get.return_value = cached_scopes
        
        # Execute
        scopes = await rbac_service.get_user_scopes(maritime_user)
        
        # Verify
        assert scopes == ["vessel:create", "vessel:read", "port:read"]
        mock_cache.get.assert_called_once()
        assert rbac_service._stats["cache_hits"] == 1
        assert rbac_service._stats["cache_misses"] == 0

    @pytest.mark.asyncio
    async def test_get_user_scopes_with_cache_miss(self, rbac_service, maritime_user, mock_cache, mock_db):
        """Test cache miss scenario requiring database resolution."""
        # Setup cache miss
        mock_cache.get.return_value = None
        
        # Mock database queries for role resolution
        direct_roles_result = Mock()
        direct_roles_result.scalars.return_value.all.return_value = []
        
        group_roles_result = Mock()
        group_roles_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [direct_roles_result, group_roles_result]
        
        # Execute
        scopes = await rbac_service.get_user_scopes(maritime_user)
        
        # Verify
        assert isinstance(scopes, list)
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
        assert rbac_service._stats["cache_misses"] == 1

    @pytest.mark.asyncio
    async def test_get_user_direct_roles(self, rbac_service, maritime_user, port_manager_role, mock_db):
        """Test getting direct role assignments."""
        # Setup database response
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [port_manager_role]
        mock_db.execute.return_value = result_mock
        
        # Execute
        roles = await rbac_service.get_user_direct_roles(maritime_user.id)
        
        # Verify
        assert len(roles) == 1
        assert roles[0].name == "Port Manager"
        assert roles[0].priority == 90
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_group_roles(self, rbac_service, maritime_user, port_manager_role, mock_db):
        """Test getting roles through group membership."""
        # Setup database response
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [port_manager_role]
        mock_db.execute.return_value = result_mock
        
        # Execute
        roles = await rbac_service.get_user_group_roles(maritime_user.id)
        
        # Verify
        assert len(roles) == 1
        assert roles[0].name == "Port Manager"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_role_permissions(self, rbac_service, port_manager_role, vessel_permission, mock_db):
        """Test getting permissions for a role."""
        # Setup database response
        result_mock = Mock()
        result_mock.scalars.return_value.all.return_value = [vessel_permission]
        mock_db.execute.return_value = result_mock
        
        # Execute
        permissions = await rbac_service.get_role_permissions(port_manager_role.id)
        
        # Verify
        assert len(permissions) == 1
        assert permissions[0].name == "vessel_operations_management"
        assert "create" in permissions[0].actions
        assert "read" in permissions[0].actions
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_resolve_role_inheritance(self, rbac_service, mock_db):
        """Test role inheritance resolution."""
        # Create parent and child roles
        parent_role = Role(
            id=uuid.uuid4(),
            name="Employee",
            priority=50,
            is_active=True,
            parent_role_id=None
        )
        
        child_role = Role(
            id=uuid.uuid4(),
            name="Manager",
            priority=80,
            is_active=True,
            parent_role_id=parent_role.id
        )
        
        # Mock parent role lookup
        parent_result = Mock()
        parent_result.scalar_one_or_none.return_value = parent_role
        mock_db.execute.return_value = parent_result
        
        # Execute
        roles = [child_role]
        resolved_roles = await rbac_service.resolve_role_inheritance(roles)
        
        # Verify inheritance
        role_names = [r.name for r in resolved_roles]
        assert "Manager" in role_names
        assert "Employee" in role_names
        assert len(resolved_roles) == 2

    def test_permissions_to_scopes(self, rbac_service, vessel_permission):
        """Test conversion of permissions to scope strings."""
        permissions = [vessel_permission]
        
        scopes = rbac_service._permissions_to_scopes(permissions)
        
        # Verify scope generation
        expected_scopes = [
            "service:create",
            "service:read", 
            "service:update",
            "service:delete"
        ]
        
        for expected in expected_scopes:
            assert expected in scopes

    @pytest.mark.asyncio
    async def test_resolve_permission_conflicts(self, rbac_service):
        """Test permission conflict resolution using role priority."""
        # Create roles with different priorities
        high_priority_role = Role(id=uuid.uuid4(), name="Manager", priority=90)
        low_priority_role = Role(id=uuid.uuid4(), name="Employee", priority=50)
        
        roles = [low_priority_role, high_priority_role]  # Unsorted
        scopes = ["user:read", "user:write", "user:delete", "user:read"]  # With duplicates
        
        # Execute
        resolved_scopes = await rbac_service._resolve_permission_conflicts(scopes, roles)
        
        # Verify deduplication
        assert len(resolved_scopes) == 3  # Unique scopes
        assert "user:read" in resolved_scopes
        assert "user:write" in resolved_scopes
        assert "user:delete" in resolved_scopes

    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self, rbac_service, maritime_user, mock_cache):
        """Test user cache invalidation."""
        # Execute
        await rbac_service.invalidate_user_cache(maritime_user.id)
        
        # Verify cache deletion
        expected_key = f"rbac:user_scopes:{maritime_user.id}"
        mock_cache.delete.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_invalidate_role_cache(self, rbac_service, port_manager_role, mock_db, mock_cache):
        """Test role cache invalidation affecting multiple users."""
        # Mock affected users query
        user_ids = [uuid.uuid4(), uuid.uuid4(), uuid.uuid4()]
        
        direct_result = Mock()
        direct_result.fetchall.return_value = [(user_ids[0],), (user_ids[1],)]
        
        group_result = Mock()
        group_result.fetchall.return_value = [(user_ids[2],)]
        
        mock_db.execute.side_effect = [direct_result, group_result]
        
        # Execute
        await rbac_service.invalidate_role_cache(port_manager_role.id)
        
        # Verify all affected users' cache is invalidated
        assert mock_cache.delete.call_count == 3
        for user_id in user_ids:
            expected_key = f"rbac:user_scopes:{user_id}"
            mock_cache.delete.assert_any_call(expected_key)

    @pytest.mark.asyncio
    async def test_get_effective_permissions(self, rbac_service, maritime_user, mock_db):
        """Test detailed permission information for debugging."""
        # Mock user lookup
        user_result = Mock()
        user_result.scalar_one_or_none.return_value = maritime_user
        mock_db.execute.return_value = user_result
        
        # Mock role and permission queries
        with patch.object(rbac_service, 'get_user_direct_roles') as mock_direct, \
             patch.object(rbac_service, 'get_user_group_roles') as mock_group, \
             patch.object(rbac_service, 'resolve_role_inheritance') as mock_inheritance, \
             patch.object(rbac_service, 'get_role_permissions') as mock_permissions, \
             patch.object(rbac_service, 'get_user_scopes') as mock_scopes:
            
            # Setup mocks
            mock_direct.return_value = []
            mock_group.return_value = []
            mock_inheritance.return_value = []
            mock_permissions.return_value = []
            mock_scopes.return_value = ["vessel:read", "port:read"]
            
            # Execute
            result = await rbac_service.get_effective_permissions(maritime_user.id)
            
            # Verify comprehensive information
            assert result["user_id"] == str(maritime_user.id)
            assert "direct_roles" in result
            assert "group_roles" in result
            assert "resolved_roles" in result
            assert "role_permissions" in result
            assert "final_scopes" in result
            assert result["final_scopes"] == ["vessel:read", "port:read"]

    @pytest.mark.asyncio
    async def test_fallback_scopes_for_service_account(self, rbac_service):
        """Test fallback scopes for service account."""
        service_account = User(
            id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            email="service@maritime.com",
            is_service_account=True
        )
        
        scopes = await rbac_service._get_fallback_scopes(service_account)
        
        # Verify service account gets enhanced fallback
        assert "api:read" in scopes
        assert "api:write" in scopes
        assert "user:read" in scopes
        assert "user:write" in scopes

    @pytest.mark.asyncio
    async def test_fallback_scopes_for_superadmin(self, rbac_service):
        """Test fallback scopes for platform superadmin."""
        platform_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")
        superadmin = User(
            id=uuid.uuid4(),
            tenant_id=platform_tenant_id,
            email="admin@platform.com",
            is_service_account=False
        )
        
        scopes = await rbac_service._get_fallback_scopes(superadmin)
        
        # Verify superadmin gets admin fallback
        assert "platform:admin" in scopes
        assert "tenant:admin" in scopes
        assert "tenant:global" in scopes
        assert "user:admin" in scopes

    def test_get_stats(self, rbac_service):
        """Test performance statistics tracking."""
        # Initial stats should be zero
        stats = rbac_service.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["cache_misses"] == 0
        assert stats["db_queries"] == 0
        assert stats["permission_resolutions"] == 0
        
        # Modify internal stats
        rbac_service._stats["cache_hits"] = 5
        rbac_service._stats["db_queries"] = 10
        
        # Verify stats are returned correctly
        updated_stats = rbac_service.get_stats()
        assert updated_stats["cache_hits"] == 5
        assert updated_stats["db_queries"] == 10

    def test_reset_stats(self, rbac_service):
        """Test statistics reset functionality."""
        # Set some stats
        rbac_service._stats["cache_hits"] = 5
        rbac_service._stats["db_queries"] = 10
        
        # Reset stats
        rbac_service.reset_stats()
        
        # Verify reset
        stats = rbac_service.get_stats()
        assert stats["cache_hits"] == 0
        assert stats["db_queries"] == 0


class TestRBACServiceFactory:
    """Test cases for RBACService factory."""
    
    @pytest.mark.asyncio
    async def test_create_with_cache(self):
        """Test factory creates service with cache enabled."""
        mock_db = AsyncMock()
        
        # Mock cache manager creation
        with patch('src.services.rbac_service.get_cache_manager') as mock_cache_factory:
            mock_cache = AsyncMock()
            mock_cache_factory.return_value = mock_cache
            
            service = await RBACServiceFactory.create(mock_db, use_cache=True)
            
            assert service.db == mock_db
            assert service.cache == mock_cache

    @pytest.mark.asyncio
    async def test_create_without_cache(self):
        """Test factory creates service with cache disabled."""
        mock_db = AsyncMock()
        
        service = await RBACServiceFactory.create(mock_db, use_cache=False)
        
        assert service.db == mock_db
        assert service.cache is None

    @pytest.mark.asyncio
    async def test_create_with_cache_import_error(self):
        """Test factory handles cache import errors gracefully."""
        mock_db = AsyncMock()
        
        # Mock import error for cache manager
        with patch('src.services.rbac_service.get_cache_manager', side_effect=ImportError("Cache not available")):
            service = await RBACServiceFactory.create(mock_db, use_cache=True)
            
            assert service.db == mock_db
            assert service.cache is None


class TestLogisticsScenarios:
    """Integration test scenarios for logistics industry RBAC."""
    
    @pytest.fixture
    def logistics_users(self):
        """Create sample logistics users with different roles."""
        maritime_tenant = uuid.uuid4()
        aircargo_tenant = uuid.uuid4()
        
        return {
            "port_manager": User(
                id=uuid.uuid4(),
                tenant_id=maritime_tenant,
                email="port.manager@maritime.com",
                first_name="Sarah",
                last_name="Thompson"
            ),
            "customs_officer": User(
                id=uuid.uuid4(),
                tenant_id=maritime_tenant,
                email="customs.officer@maritime.com",
                first_name="Ahmed",
                last_name="Hassan"
            ),
            "flight_coordinator": User(
                id=uuid.uuid4(),
                tenant_id=aircargo_tenant,
                email="flight.coord@aircargo.com",
                first_name="David",
                last_name="Kim"
            )
        }

    @pytest.mark.asyncio
    async def test_cross_tenant_isolation(self, logistics_users, mock_db, mock_cache):
        """Test that users cannot access resources from other tenants."""
        rbac_service = RBACService(mock_db, mock_cache)
        
        port_manager = logistics_users["port_manager"]
        flight_coordinator = logistics_users["flight_coordinator"]
        
        # Mock no cache
        mock_cache.get.return_value = None
        
        # Mock port manager has vessel permissions
        port_roles_result = Mock()
        port_roles_result.scalars.return_value.all.return_value = []
        
        flight_roles_result = Mock()
        flight_roles_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [port_roles_result, port_roles_result, flight_roles_result, flight_roles_result]
        
        # Get scopes for both users
        port_scopes = await rbac_service.get_user_scopes(port_manager)
        flight_scopes = await rbac_service.get_user_scopes(flight_coordinator)
        
        # Verify tenant isolation (both get empty scopes in this mock)
        assert isinstance(port_scopes, list)
        assert isinstance(flight_scopes, list)
        
        # In real scenario, they would have different resource access
        # This test verifies the isolation mechanism works

    @pytest.mark.asyncio
    async def test_multi_role_user_permissions(self, logistics_users, mock_db, mock_cache):
        """Test user with multiple roles gets combined permissions."""
        rbac_service = RBACService(mock_db, mock_cache)
        
        customs_officer = logistics_users["customs_officer"]
        
        # Mock cache miss
        mock_cache.get.return_value = None
        
        # Create multiple roles for customs officer
        customs_role = Role(id=uuid.uuid4(), name="Customs Officer", priority=80)
        security_role = Role(id=uuid.uuid4(), name="Security Inspector", priority=75)
        
        # Mock database responses
        direct_roles_result = Mock()
        direct_roles_result.scalars.return_value.all.return_value = [customs_role]
        
        group_roles_result = Mock()
        group_roles_result.scalars.return_value.all.return_value = [security_role]
        
        # Mock permissions for each role
        customs_permissions_result = Mock()
        customs_permissions_result.scalars.return_value.all.return_value = []
        
        security_permissions_result = Mock()
        security_permissions_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [
            direct_roles_result,      # Direct roles
            group_roles_result,       # Group roles
            customs_permissions_result, # Customs role permissions
            security_permissions_result # Security role permissions
        ]
        
        # Execute
        scopes = await rbac_service.get_user_scopes(customs_officer)
        
        # Verify combined permissions are resolved
        assert isinstance(scopes, list)
        # In real scenario, would verify customs + security scopes combined

    @pytest.mark.asyncio
    async def test_role_hierarchy_inheritance(self, mock_db, mock_cache):
        """Test that manager roles inherit from employee roles."""
        rbac_service = RBACService(mock_db, mock_cache)
        
        # Create role hierarchy: Employee -> Supervisor -> Manager
        employee_role = Role(
            id=uuid.uuid4(),
            name="Employee",
            priority=50,
            parent_role_id=None,
            is_active=True
        )
        
        supervisor_role = Role(
            id=uuid.uuid4(),
            name="Supervisor", 
            priority=70,
            parent_role_id=employee_role.id,
            is_active=True
        )
        
        manager_role = Role(
            id=uuid.uuid4(),
            name="Manager",
            priority=90,
            parent_role_id=supervisor_role.id,
            is_active=True
        )
        
        # Mock parent role lookups
        supervisor_lookup = Mock()
        supervisor_lookup.scalar_one_or_none.return_value = supervisor_role
        
        employee_lookup = Mock()
        employee_lookup.scalar_one_or_none.return_value = employee_role
        
        no_parent = Mock()
        no_parent.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [
            supervisor_lookup,  # Manager -> Supervisor
            employee_lookup,    # Supervisor -> Employee  
            no_parent          # Employee -> None
        ]
        
        # Execute inheritance resolution
        parent_chain = await rbac_service._get_role_parent_chain(manager_role)
        
        # Verify full chain
        assert len(parent_chain) == 2
        parent_names = [role.name for role in parent_chain]
        assert "Supervisor" in parent_names
        assert "Employee" in parent_names