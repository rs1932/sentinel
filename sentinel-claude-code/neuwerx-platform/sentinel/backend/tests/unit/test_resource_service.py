"""
Unit tests for Resource Service (Module 7)
"""
import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.resource_service import ResourceService
from src.models.resource import ResourceType
from src.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceQuery, ResourceTreeResponse,
    ResourceListResponse, ResourceResponse, ResourceDetailResponse,
    ResourcePermissionResponse, ResourceStatistics
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


class TestResourceService:
    """Test cases for ResourceService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def resource_service(self, mock_db):
        """ResourceService instance with mocked database"""
        return ResourceService(mock_db)
    
    @pytest.fixture
    def sample_tenant(self):
        """Sample tenant for testing"""
        tenant_id = uuid.uuid4()
        tenant = Mock()
        tenant.id = tenant_id
        tenant.name = "Test Tenant"
        tenant.code = "TEST"
        tenant.is_active = True
        return tenant
    
    @pytest.fixture
    def sample_resource(self, sample_tenant):
        """Sample resource for testing"""
        resource_id = uuid.uuid4()
        resource = Mock()
        resource.id = resource_id
        resource.tenant_id = sample_tenant.id
        resource.type = ResourceType.APP
        resource.name = "Test App"
        resource.code = "TEST-APP"
        resource.parent_id = None
        resource.path = f"/{resource_id}/"
        resource.attributes = {"description": "Test application"}
        resource.workflow_enabled = False
        resource.workflow_config = {}
        resource.is_active = True
        resource.created_at = datetime.utcnow()
        resource.updated_at = datetime.utcnow()
        resource.get_depth.return_value = 0
        resource.hierarchy_level_name = "App"
        resource.get_ancestors.return_value = []
        return resource
    
    @pytest.fixture
    def sample_parent_resource(self, sample_tenant):
        """Sample parent resource for testing"""
        resource_id = uuid.uuid4()
        resource = Mock()
        resource.id = resource_id
        resource.tenant_id = sample_tenant.id
        resource.type = ResourceType.PRODUCT_FAMILY
        resource.name = "Test Product Family"
        resource.code = "TEST-FAMILY"
        resource.parent_id = None
        resource.path = f"/{resource_id}/"
        resource.attributes = {}
        resource.workflow_enabled = False
        resource.workflow_config = {}
        resource.is_active = True
        resource.created_at = datetime.utcnow()
        resource.updated_at = datetime.utcnow()
        resource.get_depth.return_value = 0
        resource.hierarchy_level_name = "Product Family"
        resource.get_ancestors.return_value = []
        return resource

    @pytest.mark.asyncio
    async def test_create_resource_success(self, resource_service, mock_db, sample_tenant):
        """Test successful resource creation"""
        # Setup resource data
        resource_data = ResourceCreate(
            tenant_id=sample_tenant.id,
            type=ResourceType.APP,
            name="New App",
            code="NEW-APP",
            parent_id=None,
            attributes={"description": "New application"},
            workflow_enabled=False,
            workflow_config={},
            is_active=True
        )
        
        # Mock no existing resource with same code
        existing_result = Mock()
        existing_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = existing_result
        
        # Execute
        result = await resource_service.create_resource(resource_data)
        
        # Verify database calls
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called
        
    @pytest.mark.asyncio
    async def test_create_resource_duplicate_code(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test resource creation with duplicate code"""
        # Setup resource data with same code
        resource_data = ResourceCreate(
            tenant_id=sample_tenant.id,
            type=ResourceType.APP,
            name="Duplicate App",
            code="TEST-APP",  # Same as sample_resource
            parent_id=None,
            attributes={},
            workflow_enabled=False,
            workflow_config={},
            is_active=True
        )
        
        # Mock existing resource found
        existing_result = Mock()
        existing_result.scalar_one_or_none.return_value = sample_resource
        mock_db.execute.return_value = existing_result
        
        # Execute and verify exception
        with pytest.raises(ConflictError, match="Resource code 'TEST-APP' already exists"):
            await resource_service.create_resource(resource_data)
    
    @pytest.mark.asyncio
    async def test_create_resource_with_parent(self, resource_service, mock_db, sample_tenant, sample_parent_resource):
        """Test resource creation with valid parent"""
        # Setup resource data with parent
        resource_data = ResourceCreate(
            tenant_id=sample_tenant.id,
            type=ResourceType.APP,
            name="Child App",
            code="CHILD-APP",
            parent_id=sample_parent_resource.id,
            attributes={},
            workflow_enabled=False,
            workflow_config={},
            is_active=True
        )
        
        # Mock no existing resource, parent exists
        existing_result = Mock()
        existing_result.scalar_one_or_none.return_value = None
        
        parent_result = Mock()
        parent_result.scalar_one_or_none.return_value = sample_parent_resource
        
        mock_db.execute.side_effect = [existing_result, parent_result]
        
        # Execute
        result = await resource_service.create_resource(resource_data)
        
        # Verify parent lookup and creation
        assert mock_db.execute.call_count == 2
        assert mock_db.add.called
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_create_resource_invalid_parent(self, resource_service, mock_db, sample_tenant):
        """Test resource creation with invalid parent"""
        invalid_parent_id = uuid.uuid4()
        
        # Setup resource data with invalid parent
        resource_data = ResourceCreate(
            tenant_id=sample_tenant.id,
            type=ResourceType.APP,
            name="Orphan App",
            code="ORPHAN-APP",
            parent_id=invalid_parent_id,
            attributes={},
            workflow_enabled=False,
            workflow_config={},
            is_active=True
        )
        
        # Mock no existing resource, parent not found
        existing_result = Mock()
        existing_result.scalar_one_or_none.return_value = None
        
        parent_result = Mock()
        parent_result.scalar_one_or_none.return_value = None
        
        mock_db.execute.side_effect = [existing_result, parent_result]
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match=f"Parent resource with ID {invalid_parent_id} not found"):
            await resource_service.create_resource(resource_data)

    @pytest.mark.asyncio
    async def test_get_resource_success(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test successful resource retrieval"""
        # Mock resource found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        mock_db.execute.return_value = resource_result
        
        # Execute
        result = await resource_service.get_resource(sample_resource.id, sample_tenant.id)
        
        # Verify result
        assert isinstance(result, ResourceResponse)
        assert result.id == sample_resource.id
        assert result.name == sample_resource.name

    @pytest.mark.asyncio
    async def test_get_resource_not_found(self, resource_service, mock_db, sample_tenant):
        """Test resource retrieval when resource not found"""
        resource_id = uuid.uuid4()
        
        # Mock resource not found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = resource_result
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match=f"Resource with ID {resource_id} not found"):
            await resource_service.get_resource(resource_id, sample_tenant.id)

    @pytest.mark.asyncio
    async def test_get_resource_detail(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test detailed resource retrieval"""
        # Mock resource found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        # Mock child count
        child_count_result = Mock()
        child_count_result.scalar.return_value = 2
        
        mock_db.execute.side_effect = [resource_result, resource_result, child_count_result]
        
        # Execute
        result = await resource_service.get_resource_detail(sample_resource.id, sample_tenant.id)
        
        # Verify result
        assert isinstance(result, ResourceDetailResponse)
        assert result.id == sample_resource.id
        assert result.child_count == 2

    @pytest.mark.asyncio
    async def test_list_resources_basic(self, resource_service, mock_db, sample_tenant):
        """Test basic resource listing"""
        query = ResourceQuery(
            page=1,
            limit=10,
            sort_by="name",
            sort_order="asc"
        )
        
        # Mock count and resources
        count_result = Mock()
        count_result.scalar.return_value = 5
        
        resources_result = Mock()
        resources_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [count_result, resources_result]
        
        # Execute
        result = await resource_service.list_resources(sample_tenant.id, query)
        
        # Verify result
        assert isinstance(result, ResourceListResponse)
        assert result.total == 5
        assert result.page == 1
        assert result.limit == 10

    @pytest.mark.asyncio
    async def test_list_resources_with_filters(self, resource_service, mock_db, sample_tenant):
        """Test resource listing with filters"""
        query = ResourceQuery(
            type=ResourceType.APP,
            is_active=True,
            search="test",
            page=1,
            limit=10
        )
        
        # Mock results
        count_result = Mock()
        count_result.scalar.return_value = 1
        
        resources_result = Mock()
        resources_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [count_result, resources_result]
        
        # Execute
        result = await resource_service.list_resources(sample_tenant.id, query)
        
        # Verify filtering was applied (check call count)
        assert mock_db.execute.call_count == 2

    @pytest.mark.asyncio
    async def test_update_resource_success(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test successful resource update"""
        update_data = ResourceUpdate(
            name="Updated App Name",
            attributes={"description": "Updated description"}
        )
        
        # Mock resource found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        mock_db.execute.return_value = resource_result
        
        # Execute
        result = await resource_service.update_resource(
            sample_resource.id, 
            sample_tenant.id, 
            update_data
        )
        
        # Verify database calls
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_update_resource_not_found(self, resource_service, mock_db, sample_tenant):
        """Test resource update when resource not found"""
        resource_id = uuid.uuid4()
        update_data = ResourceUpdate(name="New Name")
        
        # Mock resource not found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = resource_result
        
        # Execute and verify exception
        with pytest.raises(NotFoundError, match=f"Resource with ID {resource_id} not found"):
            await resource_service.update_resource(resource_id, sample_tenant.id, update_data)

    @pytest.mark.asyncio
    async def test_update_resource_move_to_parent(self, resource_service, mock_db, sample_tenant, sample_resource, sample_parent_resource):
        """Test moving resource to new parent"""
        update_data = ResourceUpdate(parent_id=sample_parent_resource.id)
        
        # Mock resource and new parent found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        parent_result = Mock()
        parent_result.scalar_one_or_none.return_value = sample_parent_resource
        
        # Mock no cycle detection
        cycle_result = Mock()
        cycle_result.scalar.return_value = None
        
        mock_db.execute.side_effect = [resource_result, parent_result, cycle_result]
        
        # Execute
        result = await resource_service.update_resource(
            sample_resource.id,
            sample_tenant.id,
            update_data
        )
        
        # Verify parent validation and path update
        assert mock_db.execute.call_count == 3
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_resource_circular_dependency(self, resource_service, mock_db, sample_tenant, sample_resource, sample_parent_resource):
        """Test preventing circular dependency in hierarchy"""
        # Make parent_resource a child of sample_resource
        sample_parent_resource.parent_id = sample_resource.id
        sample_parent_resource.path = f"/{sample_resource.id}/{sample_parent_resource.id}/"
        
        update_data = ResourceUpdate(parent_id=sample_parent_resource.id)
        
        # Mock resource and parent found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        parent_result = Mock()
        parent_result.scalar_one_or_none.return_value = sample_parent_resource
        
        mock_db.execute.side_effect = [resource_result, parent_result]
        
        # Mock _would_create_cycle to return True
        with patch.object(resource_service, '_would_create_cycle', return_value=True):
            # Execute and verify exception
            with pytest.raises(ValidationError, match="Moving resource would create circular dependency"):
                await resource_service.update_resource(
                    sample_resource.id,
                    sample_tenant.id,
                    update_data
                )

    @pytest.mark.asyncio
    async def test_delete_resource_success(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test successful resource deletion (soft delete)"""
        # Mock resource found and no children
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        children_result = Mock()
        children_result.scalar.return_value = 0
        
        mock_db.execute.side_effect = [resource_result, children_result]
        
        # Execute
        result = await resource_service.delete_resource(
            sample_resource.id,
            sample_tenant.id,
            cascade=False
        )
        
        # Verify soft delete
        assert result is True
        assert sample_resource.is_active is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_delete_resource_with_children_no_cascade(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test resource deletion fails when children exist and cascade=False"""
        # Mock resource found with children
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        children_result = Mock()
        children_result.scalar.return_value = 2  # Has children
        
        mock_db.execute.side_effect = [resource_result, children_result]
        
        # Execute and verify exception
        with pytest.raises(ValidationError, match="Cannot delete resource with 2 active children"):
            await resource_service.delete_resource(
                sample_resource.id,
                sample_tenant.id,
                cascade=False
            )

    @pytest.mark.asyncio
    async def test_delete_resource_cascade(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test resource deletion with cascade"""
        # Mock resource found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        # Mock descendants
        descendants_result = Mock()
        descendants_result.fetchall.return_value = [(uuid.uuid4(),), (uuid.uuid4(),)]
        
        mock_db.execute.side_effect = [resource_result, descendants_result]
        
        # Execute
        result = await resource_service.delete_resource(
            sample_resource.id,
            sample_tenant.id,
            cascade=True
        )
        
        # Verify cascade delete
        assert result is True
        assert mock_db.execute.call_count == 3  # resource, descendants, bulk update
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_resource_tree_full(self, resource_service, mock_db, sample_tenant):
        """Test getting full resource tree"""
        # Mock resources for tree building
        resources_result = Mock()
        resources_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = resources_result
        
        # Execute
        result = await resource_service.get_resource_tree(sample_tenant.id)
        
        # Verify result
        assert isinstance(result, ResourceTreeResponse)
        assert result.total_nodes == 0
        assert result.max_depth == 0

    @pytest.mark.asyncio
    async def test_get_resource_tree_with_root(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test getting resource subtree from specific root"""
        # Mock root resource found
        root_result = Mock()
        root_result.scalar_one_or_none.return_value = sample_resource
        
        # Mock tree resources
        tree_result = Mock()
        tree_result.scalars.return_value.all.return_value = [sample_resource]
        
        mock_db.execute.side_effect = [root_result, tree_result]
        
        # Execute
        result = await resource_service.get_resource_tree(
            sample_tenant.id,
            root_id=sample_resource.id
        )
        
        # Verify result
        assert isinstance(result, ResourceTreeResponse)
        assert result.total_nodes == 1

    @pytest.mark.asyncio
    async def test_get_resource_permissions(self, resource_service, mock_db, sample_tenant, sample_resource):
        """Test getting resource permissions"""
        # Mock resource found
        resource_result = Mock()
        resource_result.scalar_one_or_none.return_value = sample_resource
        
        # Mock permissions
        permissions_result = Mock()
        permissions_result.scalars.return_value.all.return_value = []
        
        mock_db.execute.side_effect = [resource_result, permissions_result]
        
        # Execute
        result = await resource_service.get_resource_permissions(
            sample_resource.id,
            sample_tenant.id
        )
        
        # Verify result
        assert isinstance(result, ResourcePermissionResponse)
        assert result.resource_id == sample_resource.id
        assert result.resource_name == sample_resource.name

    @pytest.mark.asyncio
    async def test_get_resource_statistics(self, resource_service, mock_db, sample_tenant):
        """Test getting resource statistics"""
        # Mock statistics queries
        total_result = Mock()
        total_result.scalar.return_value = 10
        
        active_result = Mock()
        active_result.scalar.return_value = 8
        
        type_result = Mock()
        type_result.fetchall.return_value = [('app', 5), ('service', 3)]
        
        depth_result = Mock()
        depth_result.scalar.return_value = 4
        
        root_result = Mock()
        root_result.scalar.return_value = 2
        
        mock_db.execute.side_effect = [
            total_result, active_result, type_result, depth_result, root_result
        ]
        
        # Execute
        result = await resource_service.get_resource_statistics(sample_tenant.id)
        
        # Verify result
        assert isinstance(result, ResourceStatistics)
        assert result.total_resources == 10
        assert result.active_resources == 8
        assert result.inactive_resources == 2
        assert result.by_type == {'app': 5, 'service': 3}
        assert result.total_root_resources == 2

    def test_validate_hierarchy_rules_valid(self, resource_service):
        """Test valid hierarchy rules"""
        # This should not raise an exception
        # APP can be child of PRODUCT_FAMILY
        import asyncio
        asyncio.run(resource_service._validate_hierarchy_rules(
            ResourceType.APP, 
            ResourceType.PRODUCT_FAMILY
        ))

    def test_validate_hierarchy_rules_invalid(self, resource_service):
        """Test invalid hierarchy rules"""
        # This should raise ValidationError
        # PRODUCT_FAMILY cannot be child of APP
        with pytest.raises(ValidationError, match="Invalid hierarchy"):
            import asyncio
            asyncio.run(resource_service._validate_hierarchy_rules(
                ResourceType.PRODUCT_FAMILY, 
                ResourceType.APP
            ))

    @pytest.mark.asyncio
    async def test_would_create_cycle_detection(self, resource_service, mock_db):
        """Test circular dependency detection"""
        resource_id = uuid.uuid4()
        parent_id = uuid.uuid4()
        
        # Mock parent path containing the resource being moved
        parent_result = Mock()
        parent_result.scalar.return_value = f"/{resource_id}/some/path/"
        mock_db.execute.return_value = parent_result
        
        # Execute
        result = await resource_service._would_create_cycle(resource_id, parent_id)
        
        # Verify cycle detected
        assert result is True

    def test_build_tree_from_resources(self, resource_service, sample_resource):
        """Test tree building from flat resource list"""
        # Create child resource mock
        child_id = uuid.uuid4()
        child_resource = Mock()
        child_resource.id = child_id
        child_resource.tenant_id = sample_resource.tenant_id
        child_resource.type = ResourceType.SERVICE
        child_resource.name = "Child Service"
        child_resource.code = "CHILD-SERVICE"
        child_resource.parent_id = sample_resource.id
        child_resource.path = f"/{sample_resource.id}/{child_id}/"
        child_resource.attributes = {}
        child_resource.workflow_enabled = False
        child_resource.workflow_config = {}
        child_resource.is_active = True
        
        resources = [sample_resource, child_resource]
        
        # Execute
        tree = resource_service._build_tree_from_resources(resources, sample_resource.id)
        
        # Verify tree structure
        assert tree is not None
        assert tree.id == sample_resource.id
        assert len(tree.children) == 1
        assert tree.children[0].id == child_id