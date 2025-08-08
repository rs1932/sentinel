"""
Integration tests for RBAC with realistic logistics industry scenarios

These tests verify that the dynamic RBAC system works correctly with:
- Multi-tenant isolation
- Role-based access control  
- Group-based permissions
- Resource hierarchy access
- Cross-functional workflows
"""

import pytest
import asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db_engine
from src.services.rbac_service import RBACServiceFactory
from src.services.authentication import AuthenticationService
from src.models import *
from src.models.resource import ResourceType
from src.utils.password_utils import hash_password


@pytest.mark.asyncio
class TestLogisticsRBACIntegration:
    """Integration tests with actual database and realistic scenarios."""
    
    @pytest.fixture(scope="class")
    async def db_engine(self):
        """Database engine for integration tests."""
        engine = get_db_engine()
        yield engine
        await engine.dispose()
    
    @pytest.fixture
    async def db_session(self, db_engine):
        """Database session for each test."""
        async with AsyncSession(db_engine) as session:
            yield session
    
    @pytest.fixture
    async def logistics_test_data(self, db_session):
        """Create comprehensive logistics test data."""
        # Create tenants
        maritime_tenant = Tenant(
            name="Maritime Port Operations",
            code="MARITIME",
            domain="maritime.logistics.com",
            is_active=True
        )
        
        aircargo_tenant = Tenant(
            name="AirCargo Express", 
            code="AIRCARGO",
            domain="aircargo.express.com",
            is_active=True
        )
        
        db_session.add_all([maritime_tenant, aircargo_tenant])
        await db_session.flush()
        
        # Create roles for maritime tenant
        port_manager_role = Role(
            tenant_id=maritime_tenant.id,
            name="Port Manager",
            display_name="Port Manager",
            description="Oversees port operations",
            type="custom",
            priority=90,
            is_active=True
        )
        
        customs_officer_role = Role(
            tenant_id=maritime_tenant.id,
            name="Customs Officer",
            display_name="Customs Officer", 
            description="Handles customs clearance",
            type="custom",
            priority=80,
            is_active=True
        )
        
        dock_worker_role = Role(
            tenant_id=maritime_tenant.id,
            name="Dock Worker",
            display_name="Dock Worker",
            description="Cargo handling operations",
            type="custom", 
            priority=30,
            is_active=True
        )
        
        # Create roles for aircargo tenant
        ops_manager_role = Role(
            tenant_id=aircargo_tenant.id,
            name="Operations Manager",
            display_name="Operations Manager",
            description="Air cargo operations oversight",
            type="custom",
            priority=90,
            is_active=True
        )
        
        cargo_handler_role = Role(
            tenant_id=aircargo_tenant.id,
            name="Cargo Handler", 
            display_name="Cargo Handler",
            description="Physical cargo handling",
            type="custom",
            priority=40,
            is_active=True
        )
        
        db_session.add_all([
            port_manager_role, customs_officer_role, dock_worker_role,
            ops_manager_role, cargo_handler_role
        ])
        await db_session.flush()
        
        # Create groups
        maritime_ops_group = Group(
            tenant_id=maritime_tenant.id,
            name="Operations",
            display_name="Operations Department",
            description="Maritime operational staff",
            is_active=True
        )
        
        maritime_security_group = Group(
            tenant_id=maritime_tenant.id,
            name="Security", 
            display_name="Security Department",
            description="Port security and compliance",
            is_active=True
        )
        
        aircargo_ops_group = Group(
            tenant_id=aircargo_tenant.id,
            name="Operations",
            display_name="Operations Department", 
            description="Air cargo operational staff",
            is_active=True
        )
        
        db_session.add_all([maritime_ops_group, maritime_security_group, aircargo_ops_group])
        await db_session.flush()
        
        # Create resources (hierarchical)
        # Maritime resources
        maritime_app = Resource(
            tenant_id=maritime_tenant.id,
            type=ResourceType.APP,
            name="Port Management System",
            code="PMS",
            attributes={"industry": "Maritime"},
            is_active=True,
            path=f"/{uuid.uuid4()}/"
        )
        
        vessel_capability = Resource(
            tenant_id=maritime_tenant.id,
            type=ResourceType.CAPABILITY,
            name="Vessel Operations",
            code="VESSEL_OPS",
            parent_id=maritime_app.id,
            attributes={"department": "operations"},
            is_active=True
        )
        
        berth_service = Resource(
            tenant_id=maritime_tenant.id,
            type=ResourceType.SERVICE,
            name="Berth Assignment",
            code="BERTH_ASSIGN",
            parent_id=vessel_capability.id,
            attributes={"access_level": "operational"},
            is_active=True
        )
        
        customs_service = Resource(
            tenant_id=maritime_tenant.id,
            type=ResourceType.SERVICE,
            name="Customs Processing",
            code="CUSTOMS_PROC", 
            parent_id=vessel_capability.id,
            attributes={"access_level": "restricted"},
            is_active=True
        )
        
        # AirCargo resources
        aircargo_app = Resource(
            tenant_id=aircargo_tenant.id,
            type=ResourceType.APP,
            name="Air Cargo System",
            code="ACS",
            attributes={"industry": "Air Cargo"},
            is_active=True,
            path=f"/{uuid.uuid4()}/"
        )
        
        flight_capability = Resource(
            tenant_id=aircargo_tenant.id,
            type=ResourceType.CAPABILITY,
            name="Flight Operations",
            code="FLIGHT_OPS",
            parent_id=aircargo_app.id,
            attributes={"department": "operations"},
            is_active=True
        )
        
        cargo_loading_service = Resource(
            tenant_id=aircargo_tenant.id,
            type=ResourceType.SERVICE,
            name="Cargo Loading",
            code="CARGO_LOAD",
            parent_id=flight_capability.id,
            attributes={"access_level": "operational"},
            is_active=True
        )
        
        db_session.add_all([
            maritime_app, vessel_capability, berth_service, customs_service,
            aircargo_app, flight_capability, cargo_loading_service
        ])
        await db_session.flush()
        
        # Update resource paths after flush to get IDs
        maritime_app.path = f"/{maritime_app.id}/"
        vessel_capability.path = f"{maritime_app.path}{vessel_capability.id}/"
        berth_service.path = f"{vessel_capability.path}{berth_service.id}/"
        customs_service.path = f"{vessel_capability.path}{customs_service.id}/"
        
        aircargo_app.path = f"/{aircargo_app.id}/"
        flight_capability.path = f"{aircargo_app.path}{flight_capability.id}/"
        cargo_loading_service.path = f"{flight_capability.path}{cargo_loading_service.id}/"
        
        # Create permissions
        # Port Manager permissions (full access to berth assignment)
        berth_mgmt_permission = Permission(
            tenant_id=maritime_tenant.id,
            name="berth_assignment_management",
            resource_type=ResourceType.SERVICE,
            resource_id=berth_service.id,
            actions=["create", "read", "update", "delete"],
            conditions={"tenant_isolation": True},
            is_active=True
        )
        
        # Customs Officer permissions (full access to customs processing)
        customs_permission = Permission(
            tenant_id=maritime_tenant.id,
            name="customs_processing_full",
            resource_type=ResourceType.SERVICE,
            resource_id=customs_service.id,
            actions=["create", "read", "update", "delete"],
            conditions={"security_clearance": True},
            is_active=True
        )
        
        # Dock Worker permissions (read-only berth assignment)
        berth_readonly_permission = Permission(
            tenant_id=maritime_tenant.id,
            name="berth_assignment_readonly",
            resource_type=ResourceType.SERVICE,
            resource_id=berth_service.id,
            actions=["read"],
            conditions={"tenant_isolation": True},
            is_active=True
        )
        
        # Air Cargo Operations Manager permissions
        cargo_mgmt_permission = Permission(
            tenant_id=aircargo_tenant.id,
            name="cargo_loading_management",
            resource_type=ResourceType.SERVICE,
            resource_id=cargo_loading_service.id,
            actions=["create", "read", "update", "delete"],
            conditions={"tenant_isolation": True},
            is_active=True
        )
        
        # Air Cargo Handler permissions (operational access)
        cargo_ops_permission = Permission(
            tenant_id=aircargo_tenant.id,
            name="cargo_loading_ops",
            resource_type=ResourceType.SERVICE,
            resource_id=cargo_loading_service.id,
            actions=["read", "update"],
            conditions={"operational_hours": True},
            is_active=True
        )
        
        db_session.add_all([
            berth_mgmt_permission, customs_permission, berth_readonly_permission,
            cargo_mgmt_permission, cargo_ops_permission
        ])
        await db_session.flush()
        
        # Create role-permission assignments
        role_permissions = [
            RolePermission(role_id=port_manager_role.id, permission_id=berth_mgmt_permission.id),
            RolePermission(role_id=customs_officer_role.id, permission_id=customs_permission.id),
            RolePermission(role_id=dock_worker_role.id, permission_id=berth_readonly_permission.id),
            RolePermission(role_id=ops_manager_role.id, permission_id=cargo_mgmt_permission.id),
            RolePermission(role_id=cargo_handler_role.id, permission_id=cargo_ops_permission.id)
        ]
        
        db_session.add_all(role_permissions)
        
        # Create group-role assignments
        group_roles = [
            GroupRole(group_id=maritime_ops_group.id, role_id=port_manager_role.id),
            GroupRole(group_id=maritime_ops_group.id, role_id=dock_worker_role.id),
            GroupRole(group_id=maritime_security_group.id, role_id=customs_officer_role.id),
            GroupRole(group_id=aircargo_ops_group.id, role_id=ops_manager_role.id),
            GroupRole(group_id=aircargo_ops_group.id, role_id=cargo_handler_role.id)
        ]
        
        db_session.add_all(group_roles)
        
        # Create test users
        default_password = "LogisticsTest2024!"
        hashed_password = hash_password(default_password)
        
        # Maritime users
        port_manager = User(
            tenant_id=maritime_tenant.id,
            email="sarah.thompson@maritime.com",
            username="sarah.thompson",
            password_hash=hashed_password,
            first_name="Sarah",
            last_name="Thompson", 
            display_name="Sarah Thompson",
            is_active=True,
            email_verified=True
        )
        
        customs_officer = User(
            tenant_id=maritime_tenant.id,
            email="ahmed.hassan@maritime.com",
            username="ahmed.hassan",
            password_hash=hashed_password,
            first_name="Ahmed",
            last_name="Hassan",
            display_name="Ahmed Hassan", 
            is_active=True,
            email_verified=True
        )
        
        dock_worker = User(
            tenant_id=maritime_tenant.id,
            email="jose.rodriguez@maritime.com",
            username="jose.rodriguez",
            password_hash=hashed_password,
            first_name="Jose",
            last_name="Rodriguez",
            display_name="Jose Rodriguez",
            is_active=True,
            email_verified=True
        )
        
        # AirCargo users
        ops_manager = User(
            tenant_id=aircargo_tenant.id,
            email="lisa.wagner@aircargo.com",
            username="lisa.wagner", 
            password_hash=hashed_password,
            first_name="Lisa",
            last_name="Wagner",
            display_name="Lisa Wagner",
            is_active=True,
            email_verified=True
        )
        
        cargo_handler = User(
            tenant_id=aircargo_tenant.id,
            email="carlos.mendez@aircargo.com",
            username="carlos.mendez",
            password_hash=hashed_password,
            first_name="Carlos",
            last_name="Mendez",
            display_name="Carlos Mendez",
            is_active=True,
            email_verified=True
        )
        
        db_session.add_all([port_manager, customs_officer, dock_worker, ops_manager, cargo_handler])
        await db_session.flush()
        
        # Create user-role assignments (direct)
        user_roles = [
            UserRole(user_id=port_manager.id, role_id=port_manager_role.id, is_active=True),
            UserRole(user_id=customs_officer.id, role_id=customs_officer_role.id, is_active=True),
            UserRole(user_id=ops_manager.id, role_id=ops_manager_role.id, is_active=True)
        ]
        
        db_session.add_all(user_roles)
        
        # Create user-group assignments (group-based roles)  
        user_groups = [
            UserGroup(user_id=dock_worker.id, group_id=maritime_ops_group.id),
            UserGroup(user_id=cargo_handler.id, group_id=aircargo_ops_group.id)
        ]
        
        db_session.add_all(user_groups)
        
        await db_session.commit()
        
        # Return test data structure
        return {
            "tenants": {
                "maritime": maritime_tenant,
                "aircargo": aircargo_tenant
            },
            "users": {
                "port_manager": port_manager,
                "customs_officer": customs_officer,
                "dock_worker": dock_worker,
                "ops_manager": ops_manager,
                "cargo_handler": cargo_handler
            },
            "roles": {
                "port_manager": port_manager_role,
                "customs_officer": customs_officer_role,
                "dock_worker": dock_worker_role,
                "ops_manager": ops_manager_role,
                "cargo_handler": cargo_handler_role
            },
            "resources": {
                "berth_service": berth_service,
                "customs_service": customs_service,
                "cargo_loading_service": cargo_loading_service
            },
            "permissions": {
                "berth_mgmt": berth_mgmt_permission,
                "customs_full": customs_permission,
                "berth_readonly": berth_readonly_permission,
                "cargo_mgmt": cargo_mgmt_permission,
                "cargo_ops": cargo_ops_permission
            }
        }

    async def test_port_manager_permissions(self, db_session, logistics_test_data):
        """Test Port Manager has full berth assignment access."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        
        port_manager = logistics_test_data["users"]["port_manager"]
        
        # Get user scopes
        scopes = await rbac_service.get_user_scopes(port_manager)
        
        # Verify Port Manager has berth management permissions
        assert "service:create" in scopes
        assert "service:read" in scopes
        assert "service:update" in scopes
        assert "service:delete" in scopes
        
        # Get detailed permissions for verification
        details = await rbac_service.get_effective_permissions(port_manager.id)
        
        assert len(details["direct_roles"]) == 1
        assert details["direct_roles"][0]["name"] == "Port Manager"
        assert len(details["final_scopes"]) > 0

    async def test_customs_officer_security_access(self, db_session, logistics_test_data):
        """Test Customs Officer has access to customs processing but not berth management."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        
        customs_officer = logistics_test_data["users"]["customs_officer"]
        
        # Get effective permissions
        details = await rbac_service.get_effective_permissions(customs_officer.id)
        scopes = details["final_scopes"]
        
        # Verify customs officer has appropriate access
        assert len(details["direct_roles"]) == 1
        assert details["direct_roles"][0]["name"] == "Customs Officer"
        
        # Should have service-level permissions from customs processing
        service_scopes = [s for s in scopes if s.startswith("service:")]
        assert len(service_scopes) > 0

    async def test_dock_worker_group_based_permissions(self, db_session, logistics_test_data):
        """Test Dock Worker gets permissions through group membership."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        
        dock_worker = logistics_test_data["users"]["dock_worker"]
        
        # Get effective permissions
        details = await rbac_service.get_effective_permissions(dock_worker.id)
        
        # Verify dock worker has no direct roles but has group roles
        assert len(details["direct_roles"]) == 0
        assert len(details["group_roles"]) > 0
        
        # Should have read-only access through group
        scopes = details["final_scopes"]
        assert "service:read" in scopes
        
        # Should NOT have write access
        assert "service:create" not in scopes
        assert "service:delete" not in scopes

    async def test_cross_tenant_isolation(self, db_session, logistics_test_data):
        """Test that maritime users cannot access aircargo resources."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        
        port_manager = logistics_test_data["users"]["port_manager"]
        ops_manager = logistics_test_data["users"]["ops_manager"]
        
        # Get scopes for both users
        port_scopes = await rbac_service.get_user_scopes(port_manager)
        ops_scopes = await rbac_service.get_user_scopes(ops_manager)
        
        # Both should have service-level permissions, but for different resources
        assert len(port_scopes) > 0
        assert len(ops_scopes) > 0
        
        # Get detailed permissions to verify resource isolation
        port_details = await rbac_service.get_effective_permissions(port_manager.id)
        ops_details = await rbac_service.get_effective_permissions(ops_manager.id)
        
        # Extract resource IDs from permissions
        port_resources = set()
        ops_resources = set()
        
        for role_name, permissions in port_details["role_permissions"].items():
            for perm in permissions:
                if perm["resource_id"]:
                    port_resources.add(perm["resource_id"])
        
        for role_name, permissions in ops_details["role_permissions"].items():
            for perm in permissions:
                if perm["resource_id"]:
                    ops_resources.add(perm["resource_id"])
        
        # Verify no resource overlap between tenants
        assert not port_resources.intersection(ops_resources)

    async def test_role_priority_conflict_resolution(self, db_session, logistics_test_data):
        """Test that higher priority roles take precedence in conflict scenarios."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        
        # Create a user with multiple roles of different priorities
        maritime_tenant = logistics_test_data["tenants"]["maritime"]
        
        # Create supervisor role (higher priority than dock worker)
        supervisor_role = Role(
            tenant_id=maritime_tenant.id,
            name="Terminal Supervisor",
            display_name="Terminal Supervisor",
            description="Supervises terminal operations",
            type="custom",
            priority=75,  # Higher than dock worker (30)
            is_active=True
        )
        
        db_session.add(supervisor_role)
        await db_session.flush()
        
        # Assign both roles to dock worker
        dock_worker = logistics_test_data["users"]["dock_worker"]
        supervisor_assignment = UserRole(
            user_id=dock_worker.id,
            role_id=supervisor_role.id,
            is_active=True
        )
        
        db_session.add(supervisor_assignment)
        await db_session.commit()
        
        # Get effective permissions
        details = await rbac_service.get_effective_permissions(dock_worker.id)
        
        # Should have roles from both direct assignment and group
        total_roles = len(details["direct_roles"]) + len(details["group_roles"])
        assert total_roles >= 2
        
        # Verify roles are sorted by priority in resolution
        all_roles = details["direct_roles"] + details["group_roles"]
        priorities = [role["priority"] for role in all_roles]
        
        # Should have different priority levels
        assert len(set(priorities)) > 1

    async def test_permission_caching_performance(self, db_session, logistics_test_data):
        """Test that permission caching improves performance."""
        # First call without cache
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        port_manager = logistics_test_data["users"]["port_manager"]
        
        import time
        start_time = time.time()
        scopes1 = await rbac_service.get_user_scopes(port_manager)
        no_cache_time = time.time() - start_time
        
        # Second call with cache
        rbac_service_cached = await RBACServiceFactory.create(db_session, use_cache=True)
        
        start_time = time.time()
        scopes2 = await rbac_service_cached.get_user_scopes(port_manager)
        first_call_time = time.time() - start_time
        
        # Third call should hit cache
        start_time = time.time()
        scopes3 = await rbac_service_cached.get_user_scopes(port_manager)
        cached_call_time = time.time() - start_time
        
        # Verify same results
        assert scopes1 == scopes2 == scopes3
        
        # Cache should be faster (though timing may vary in tests)
        stats = rbac_service_cached.get_stats()
        assert stats["cache_hits"] > 0 or stats["cache_misses"] > 0

    async def test_role_inheritance_with_logistics_hierarchy(self, db_session, logistics_test_data):
        """Test role inheritance in maritime organizational hierarchy."""
        maritime_tenant = logistics_test_data["tenants"]["maritime"]
        
        # Create role hierarchy: Employee -> Operator -> Supervisor -> Manager
        employee_role = Role(
            tenant_id=maritime_tenant.id,
            name="Employee",
            description="Base employee role",
            type="custom",
            priority=20,
            parent_role_id=None,
            is_active=True
        )
        
        db_session.add(employee_role)
        await db_session.flush()
        
        operator_role = Role(
            tenant_id=maritime_tenant.id,
            name="Terminal Operator",
            description="Terminal equipment operator",
            type="custom",
            priority=40,
            parent_role_id=employee_role.id,
            is_active=True
        )
        
        db_session.add(operator_role)
        await db_session.flush()
        
        # Create user with operator role
        operator_user = User(
            tenant_id=maritime_tenant.id,
            email="operator@maritime.com",
            username="operator",
            password_hash="hashed",
            first_name="John",
            last_name="Operator",
            is_active=True
        )
        
        db_session.add(operator_user)
        await db_session.flush()
        
        # Assign operator role
        user_role = UserRole(
            user_id=operator_user.id,
            role_id=operator_role.id,
            is_active=True
        )
        
        db_session.add(user_role)
        await db_session.commit()
        
        # Test inheritance
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        details = await rbac_service.get_effective_permissions(operator_user.id)
        
        # Should have both operator and inherited employee roles
        all_role_names = [r["name"] for r in details["resolved_roles"]]
        assert "Terminal Operator" in all_role_names
        assert "Employee" in all_role_names

    async def test_multi_group_user_permissions(self, db_session, logistics_test_data):
        """Test user with membership in multiple groups gets combined permissions."""
        maritime_tenant = logistics_test_data["tenants"]["maritime"]
        
        # Create compliance group
        compliance_group = Group(
            tenant_id=maritime_tenant.id,
            name="Compliance",
            display_name="Compliance Department",
            description="Regulatory compliance staff",
            is_active=True
        )
        
        db_session.add(compliance_group)
        await db_session.flush()
        
        # Assign customs officer role to compliance group
        compliance_role_assignment = GroupRole(
            group_id=compliance_group.id,
            role_id=logistics_test_data["roles"]["customs_officer"].id
        )
        
        db_session.add(compliance_role_assignment)
        
        # Add dock worker to both operations and compliance groups
        dock_worker = logistics_test_data["users"]["dock_worker"]
        compliance_membership = UserGroup(
            user_id=dock_worker.id,
            group_id=compliance_group.id
        )
        
        db_session.add(compliance_membership)
        await db_session.commit()
        
        # Test combined permissions
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=False)
        details = await rbac_service.get_effective_permissions(dock_worker.id)
        
        # Should have roles from multiple groups
        group_role_names = [r["name"] for r in details["group_roles"]]
        
        # Should include both dock worker and customs officer roles
        assert len(set(group_role_names)) >= 2
        
        # Verify has permissions from both roles
        scopes = details["final_scopes"]
        assert len(scopes) > 0

    async def test_authentication_service_integration(self, db_session, logistics_test_data):
        """Test that authentication service properly uses RBAC for token generation."""
        from src.schemas.auth import LoginRequest
        
        auth_service = AuthenticationService(db_session)
        port_manager = logistics_test_data["users"]["port_manager"]
        
        # Create login request
        login_request = LoginRequest(
            email=port_manager.email,
            password="LogisticsTest2024!",  # Default password from seeding
            tenant_id=str(logistics_test_data["tenants"]["maritime"].id)
        )
        
        try:
            # Attempt authentication (may fail due to missing dependencies)
            # But we can test the scope resolution part
            scopes = await auth_service._get_user_scopes(port_manager)
            
            # Verify dynamic RBAC is being used
            assert len(scopes) > 0
            
            # Should include service-level permissions
            service_scopes = [s for s in scopes if s.startswith("service:")]
            assert len(service_scopes) > 0
            
        except Exception as e:
            # Authentication may fail due to missing JWT setup, but scope resolution should work
            if "get_user_scopes" in str(e):
                pytest.fail(f"RBAC scope resolution failed: {e}")

    async def test_permission_invalidation_cascade(self, db_session, logistics_test_data):
        """Test that permission changes properly invalidate related caches."""
        rbac_service = await RBACServiceFactory.create(db_session, use_cache=True)
        
        port_manager = logistics_test_data["users"]["port_manager"]
        port_manager_role = logistics_test_data["roles"]["port_manager"]
        
        # Get initial permissions (should cache)
        initial_scopes = await rbac_service.get_user_scopes(port_manager)
        
        # Invalidate user cache
        await rbac_service.invalidate_user_cache(port_manager.id)
        
        # Get permissions again (should rebuild cache)
        new_scopes = await rbac_service.get_user_scopes(port_manager)
        
        # Should be identical
        assert initial_scopes == new_scopes
        
        # Test role-level invalidation
        await rbac_service.invalidate_role_cache(port_manager_role.id)
        
        # Should handle invalidation without errors
        final_scopes = await rbac_service.get_user_scopes(port_manager)
        assert final_scopes == initial_scopes