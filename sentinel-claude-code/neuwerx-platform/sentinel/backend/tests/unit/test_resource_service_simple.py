"""
Simple unit tests for Resource Service (Module 7) - Core business logic
"""
import pytest
import uuid
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from src.services.resource_service import ResourceService
from src.models.resource import ResourceType
from src.schemas.resource import (
    ResourceCreate, ResourceUpdate, ResourceQuery,
    ResourceResponse, ResourceDetailResponse, ResourceListResponse,
    ResourceTreeResponse, ResourcePermissionResponse, ResourceStatistics
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


@pytest.fixture
def mock_db():
    """Mock database session"""
    return AsyncMock()


@pytest.fixture
def resource_service(mock_db):
    """ResourceService instance with mocked database"""
    return ResourceService(mock_db)


@pytest.fixture
def sample_tenant_id():
    """Sample tenant ID"""
    return uuid.uuid4()


@pytest.fixture
def sample_resource_data(sample_tenant_id):
    """Sample resource creation data"""
    return ResourceCreate(
        tenant_id=sample_tenant_id,
        type=ResourceType.APP,
        name="Test App",
        code="TEST-APP",
        parent_id=None,
        attributes={"description": "Test application"},
        workflow_enabled=False,
        workflow_config={},
        is_active=True
    )


@pytest.mark.asyncio
@patch('src.services.resource_service.Resource')
@patch('src.services.resource_service.ResourceResponse')
async def test_create_resource_success(mock_response, mock_resource_class, resource_service, mock_db, sample_resource_data):
    """Test successful resource creation"""
    # Mock no existing resource with same code
    existing_result = Mock()
    existing_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = existing_result
    
    # Mock Resource creation
    mock_resource_instance = Mock()
    mock_resource_instance.id = uuid.uuid4()
    mock_resource_instance.path = f"/{mock_resource_instance.id}/"
    mock_resource_class.return_value = mock_resource_instance
    
    # Mock ResourceResponse.model_validate
    mock_response.model_validate.return_value = Mock()
    
    # Execute
    await resource_service.create_resource(sample_resource_data)
    
    # Verify database calls
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called
    assert mock_resource_class.called


@pytest.mark.asyncio
async def test_create_resource_duplicate_code(resource_service, mock_db, sample_resource_data):
    """Test resource creation with duplicate code"""
    # Mock existing resource found
    existing_resource = Mock()
    existing_result = Mock()
    existing_result.scalar_one_or_none.return_value = existing_resource
    mock_db.execute.return_value = existing_result
    
    # Execute and verify exception
    with pytest.raises(ConflictError, match="Resource code 'TEST-APP' already exists"):
        await resource_service.create_resource(sample_resource_data)


@pytest.mark.asyncio
async def test_get_resource_success(resource_service, mock_db, sample_tenant_id):
    """Test successful resource retrieval"""
    resource_id = uuid.uuid4()
    
    # Mock resource found
    mock_resource = Mock()
    mock_resource.id = resource_id
    mock_resource.name = "Test App"
    
    resource_result = Mock()
    resource_result.scalar_one_or_none.return_value = mock_resource
    mock_db.execute.return_value = resource_result
    
    # Mock ResourceResponse
    with patch('src.services.resource_service.ResourceResponse') as mock_response:
        expected_response = Mock()
        expected_response.id = resource_id
        expected_response.name = "Test App"
        mock_response.model_validate.return_value = expected_response
        
        # Execute
        result = await resource_service.get_resource(resource_id, sample_tenant_id)
        
        # Verify
        assert result.id == resource_id
        assert result.name == "Test App"


@pytest.mark.asyncio
async def test_get_resource_not_found(resource_service, mock_db, sample_tenant_id):
    """Test resource retrieval when resource not found"""
    resource_id = uuid.uuid4()
    
    # Mock resource not found
    resource_result = Mock()
    resource_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = resource_result
    
    # Execute and verify exception
    with pytest.raises(NotFoundError, match=f"Resource with ID {resource_id} not found"):
        await resource_service.get_resource(resource_id, sample_tenant_id)


@pytest.mark.asyncio
async def test_list_resources_basic(resource_service, mock_db, sample_tenant_id):
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
    
    # Mock ResourceListResponse
    with patch('src.services.resource_service.ResourceListResponse') as mock_response:
        expected_response = Mock()
        expected_response.total = 5
        expected_response.page = 1
        expected_response.limit = 10
        mock_response.return_value = expected_response
        
        # Execute
        result = await resource_service.list_resources(sample_tenant_id, query)
        
        # Verify
        assert result.total == 5
        assert result.page == 1
        assert result.limit == 10


@pytest.mark.asyncio
async def test_update_resource_success(resource_service, mock_db, sample_tenant_id):
    """Test successful resource update"""
    resource_id = uuid.uuid4()
    update_data = ResourceUpdate(
        name="Updated App Name",
        attributes={"description": "Updated description"}
    )
    
    # Mock resource found
    mock_resource = Mock()
    mock_resource.id = resource_id
    mock_resource.name = "Updated App Name"
    
    resource_result = Mock()
    resource_result.scalar_one_or_none.return_value = mock_resource
    mock_db.execute.return_value = resource_result
    
    # Mock ResourceResponse
    with patch('src.services.resource_service.ResourceResponse') as mock_response:
        expected_response = Mock()
        expected_response.id = resource_id
        mock_response.model_validate.return_value = expected_response
        
        # Execute
        result = await resource_service.update_resource(
            resource_id,
            sample_tenant_id,
            update_data
        )
        
        # Verify database calls
        assert mock_db.commit.called
        assert mock_db.refresh.called
        assert result.id == resource_id


@pytest.mark.asyncio
async def test_delete_resource_success(resource_service, mock_db, sample_tenant_id):
    """Test successful resource deletion (soft delete)"""
    resource_id = uuid.uuid4()
    
    # Mock resource found and no children
    mock_resource = Mock()
    mock_resource.id = resource_id
    mock_resource.is_active = True
    
    resource_result = Mock()
    resource_result.scalar_one_or_none.return_value = mock_resource
    
    children_result = Mock()
    children_result.scalar.return_value = 0
    
    mock_db.execute.side_effect = [resource_result, children_result]
    
    # Execute
    result = await resource_service.delete_resource(
        resource_id,
        sample_tenant_id,
        cascade=False
    )
    
    # Verify soft delete
    assert result is True
    assert mock_resource.is_active is False
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_delete_resource_with_children_no_cascade(resource_service, mock_db, sample_tenant_id):
    """Test resource deletion fails when children exist and cascade=False"""
    resource_id = uuid.uuid4()
    
    # Mock resource found with children
    mock_resource = Mock()
    resource_result = Mock()
    resource_result.scalar_one_or_none.return_value = mock_resource
    
    children_result = Mock()
    children_result.scalar.return_value = 2  # Has children
    
    mock_db.execute.side_effect = [resource_result, children_result]
    
    # Execute and verify exception
    with pytest.raises(ValidationError, match="Cannot delete resource with 2 active children"):
        await resource_service.delete_resource(
            resource_id,
            sample_tenant_id,
            cascade=False
        )


@pytest.mark.asyncio
async def test_get_resource_tree_basic(resource_service, mock_db, sample_tenant_id):
    """Test getting resource tree"""
    # Mock resources for tree building
    resources_result = Mock()
    resources_result.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = resources_result
    
    # Mock ResourceTreeResponse
    with patch('src.services.resource_service.ResourceTreeResponse') as mock_response:
        expected_response = Mock()
        expected_response.total_nodes = 0
        expected_response.max_depth = 0
        mock_response.return_value = expected_response
        
        # Execute
        result = await resource_service.get_resource_tree(sample_tenant_id)
        
        # Verify result
        assert result.total_nodes == 0
        assert result.max_depth == 0


@pytest.mark.asyncio
async def test_get_resource_statistics(resource_service, mock_db, sample_tenant_id):
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
    
    # Mock ResourceStatistics
    with patch('src.services.resource_service.ResourceStatistics') as mock_stats:
        expected_stats = Mock()
        expected_stats.total_resources = 10
        expected_stats.active_resources = 8
        expected_stats.inactive_resources = 2
        expected_stats.by_type = {'app': 5, 'service': 3}
        mock_stats.return_value = expected_stats
        
        # Execute
        result = await resource_service.get_resource_statistics(sample_tenant_id)
        
        # Verify result
        assert result.total_resources == 10
        assert result.active_resources == 8
        assert result.inactive_resources == 2


def test_validate_hierarchy_rules_valid():
    """Test valid hierarchy rules"""
    service = ResourceService(None)  # DB not needed for this test
    
    # This should not raise an exception
    # APP can be child of PRODUCT_FAMILY
    import asyncio
    asyncio.run(service._validate_hierarchy_rules(
        ResourceType.APP,
        ResourceType.PRODUCT_FAMILY
    ))


@pytest.mark.asyncio
async def test_validate_hierarchy_rules_invalid():
    """Test invalid hierarchy rules"""
    service = ResourceService(None)  # DB not needed for this test
    
    # This should raise ValidationError
    # PRODUCT_FAMILY cannot be child of APP
    with pytest.raises(ValidationError, match="Invalid hierarchy"):
        await service._validate_hierarchy_rules(
            ResourceType.PRODUCT_FAMILY,
            ResourceType.APP
        )


@pytest.mark.asyncio
async def test_would_create_cycle_detection(resource_service, mock_db):
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


def test_build_tree_from_resources():
    """Test tree building from flat resource list"""
    service = ResourceService(None)  # DB not needed for this test
    
    # Create mock resources
    root_id = uuid.uuid4()
    child_id = uuid.uuid4()
    
    root_resource = Mock()
    root_resource.id = root_id
    root_resource.parent_id = None
    root_resource.type = ResourceType.APP
    root_resource.name = "Root App"
    root_resource.code = "ROOT-APP"
    root_resource.attributes = {}
    root_resource.is_active = True
    
    child_resource = Mock()
    child_resource.id = child_id
    child_resource.parent_id = root_id
    child_resource.type = ResourceType.SERVICE
    child_resource.name = "Child Service"
    child_resource.code = "CHILD-SERVICE"
    child_resource.attributes = {}
    child_resource.is_active = True
    
    resources = [root_resource, child_resource]
    
    # Execute
    tree = service._build_tree_from_resources(resources, root_id)
    
    # Verify tree structure
    assert tree is not None
    assert tree.id == root_id
    assert len(tree.children) == 1
    assert tree.children[0].id == child_id