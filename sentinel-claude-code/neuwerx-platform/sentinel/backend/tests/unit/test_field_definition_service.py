"""
Unit tests for FieldDefinitionService (Module 8)
Tests the service layer logic for field definition management
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from src.services.field_definition_service import FieldDefinitionService
from src.schemas.field_definition import (
    FieldDefinitionCreate, FieldDefinitionUpdate, FieldDefinitionQuery
)
from src.models import FieldDefinition, FieldType, FieldDataType, FieldPermission
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


class TestFieldDefinitionService:
    """Test FieldDefinitionService methods."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return AsyncMock()
    
    @pytest.fixture
    def field_service(self, mock_db):
        """Create FieldDefinitionService instance."""
        return FieldDefinitionService(mock_db)
    
    @pytest.fixture
    def sample_field_create(self):
        """Sample field definition create data."""
        return FieldDefinitionCreate(
            tenant_id=uuid4(),
            entity_type="vessel",
            field_name="test_field",
            field_type=FieldType.PLATFORM_DYNAMIC.value,
            data_type=FieldDataType.STRING.value,
            storage_path="custom_attributes.test_field",
            display_name="Test Field",
            description="A test field",
            validation_rules={"max_length": 100},
            default_visibility=FieldPermission.READ.value
        )
    
    @pytest.fixture
    def sample_field_definition(self, sample_field_create):
        """Sample field definition model instance."""
        field_def = FieldDefinition(
            id=uuid4(),
            tenant_id=sample_field_create.tenant_id,
            entity_type=sample_field_create.entity_type,
            field_name=sample_field_create.field_name,
            field_type=sample_field_create.field_type,
            data_type=sample_field_create.data_type,
            storage_path=sample_field_create.storage_path,
            display_name=sample_field_create.display_name,
            description=sample_field_create.description,
            validation_rules=sample_field_create.validation_rules,
            default_visibility=sample_field_create.default_visibility,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        return field_def

    @pytest.mark.asyncio
    async def test_create_field_definition_success(self, field_service, mock_db, sample_field_create):
        """Test successful field definition creation."""
        # Mock database responses
        mock_db.execute.return_value.scalar_one_or_none.return_value = None  # No existing definition
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock field definition instance
        mock_field_def = MagicMock()
        mock_field_def.id = uuid4()
        mock_field_def.tenant_id = sample_field_create.tenant_id
        mock_field_def.entity_type = sample_field_create.entity_type
        mock_field_def.field_name = sample_field_create.field_name
        mock_field_def.field_type = sample_field_create.field_type
        mock_field_def.data_type = sample_field_create.data_type
        mock_field_def.created_at = datetime.now(timezone.utc)
        mock_field_def.updated_at = datetime.now(timezone.utc)
        
        mock_db.add = MagicMock()
        mock_db.refresh.side_effect = lambda x: setattr(x, 'id', mock_field_def.id)
        
        # Execute
        result = await field_service.create_field_definition(sample_field_create)
        
        # Verify
        assert mock_db.add.called
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_create_field_definition_duplicate_error(self, field_service, mock_db, sample_field_create):
        """Test field definition creation with duplicate error."""
        # Mock existing field definition found
        existing_def = MagicMock()
        mock_db.execute.return_value.scalar_one_or_none.return_value = existing_def
        
        # Execute and verify exception
        with pytest.raises(ConflictError) as exc_info:
            await field_service.create_field_definition(sample_field_create)
        
        assert "already exists" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_field_definition_validation_error(self, field_service, mock_db):
        """Test field definition creation with validation errors."""
        # Test core field without storage_column
        invalid_field_data = FieldDefinitionCreate(
            tenant_id=uuid4(),
            entity_type="vessel",
            field_name="invalid_field",
            field_type=FieldType.CORE.value,
            data_type=FieldDataType.STRING.value,
            storage_path="should_not_be_set",  # Invalid for core field
            default_visibility=FieldPermission.READ.value
        )
        
        # Mock no existing definition
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify validation error
        with pytest.raises(ValidationError) as exc_info:
            await field_service.create_field_definition(invalid_field_data)
        
        assert "storage_column is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_field_definition_success(self, field_service, mock_db, sample_field_definition):
        """Test successful field definition retrieval."""
        # Mock database response
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_field_definition
        
        # Execute
        result = await field_service.get_field_definition(sample_field_definition.id)
        
        # Verify result structure
        assert result.id == sample_field_definition.id
        assert result.field_name == sample_field_definition.field_name
        assert hasattr(result, 'is_platform_wide')
        assert hasattr(result, 'full_field_path')
        assert hasattr(result, 'storage_info')

    @pytest.mark.asyncio
    async def test_get_field_definition_not_found(self, field_service, mock_db):
        """Test field definition retrieval with not found error."""
        fake_id = uuid4()
        
        # Mock database response - not found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError) as exc_info:
            await field_service.get_field_definition(fake_id)
        
        assert str(fake_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_field_definitions(self, field_service, mock_db, sample_field_definition):
        """Test field definition listing with filters."""
        query_params = FieldDefinitionQuery(
            entity_type="vessel",
            field_type="platform_dynamic",
            page=1,
            limit=10
        )
        
        # Mock database responses
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=1)),  # Total count
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[sample_field_definition]))))  # Results
        ]
        
        # Execute
        result = await field_service.list_field_definitions(query_params)
        
        # Verify
        assert result.total == 1
        assert len(result.items) == 1
        assert result.page == 1
        assert result.limit == 10

    @pytest.mark.asyncio
    async def test_update_field_definition_success(self, field_service, mock_db, sample_field_definition):
        """Test successful field definition update."""
        update_data = FieldDefinitionUpdate(
            display_name="Updated Display Name",
            description="Updated description"
        )
        
        # Mock database response
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_field_definition
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Execute
        result = await field_service.update_field_definition(sample_field_definition.id, update_data)
        
        # Verify
        assert mock_db.commit.called
        assert mock_db.refresh.called

    @pytest.mark.asyncio
    async def test_update_field_definition_not_found(self, field_service, mock_db):
        """Test field definition update with not found error."""
        fake_id = uuid4()
        update_data = FieldDefinitionUpdate(display_name="Updated")
        
        # Mock database response - not found
        mock_db.execute.return_value.scalar_one_or_none.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundError):
            await field_service.update_field_definition(fake_id, update_data)

    @pytest.mark.asyncio
    async def test_delete_field_definition_success(self, field_service, mock_db, sample_field_definition):
        """Test successful field definition deletion (soft delete)."""
        # Mock database response
        mock_db.execute.return_value.scalar_one_or_none.return_value = sample_field_definition
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await field_service.delete_field_definition(sample_field_definition.id)
        
        # Verify
        assert result is True
        assert sample_field_definition.is_active is False
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_get_field_definitions_by_entity(self, field_service, mock_db, sample_field_definition):
        """Test getting field definitions by entity type."""
        # Mock database response
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_field_definition]
        
        # Execute
        result = await field_service.get_field_definitions_by_entity("vessel")
        
        # Verify
        assert len(result) == 1
        assert result[0].entity_type == "vessel"

    @pytest.mark.asyncio
    async def test_check_field_permissions(self, field_service, mock_db, sample_field_definition):
        """Test field permission checking."""
        user_id = uuid4()
        entity_type = "vessel"
        fields = ["test_field"]
        
        # Mock field definitions response
        mock_db.execute.return_value.scalars.return_value.all.return_value = [sample_field_definition]
        
        # Execute
        result = await field_service.check_field_permissions(user_id, entity_type, None, fields)
        
        # Verify
        assert result.user_id == user_id
        assert result.entity_type == entity_type
        assert "field_permissions" in result.dict()
        assert result.checked_fields == fields

    @pytest.mark.asyncio
    async def test_get_statistics(self, field_service, mock_db):
        """Test field definition statistics retrieval."""
        # Mock multiple database calls for statistics
        mock_db.execute.side_effect = [
            MagicMock(scalar=MagicMock(return_value=10)),  # total_definitions
            MagicMock(scalar=MagicMock(return_value=8)),   # active_definitions
            MagicMock(scalar=MagicMock(return_value=2)),   # platform_wide_definitions
            MagicMock(fetchall=MagicMock(return_value=[MagicMock(entity_type="vessel", count=5)])),  # by_entity_type
            MagicMock(fetchall=MagicMock(return_value=[MagicMock(field_type="core", count=3)])),    # by_field_type
            MagicMock(fetchall=MagicMock(return_value=[MagicMock(data_type="string", count=7)]))    # by_data_type
        ]
        
        # Execute
        result = await field_service.get_statistics()
        
        # Verify
        assert result.total_definitions == 10
        assert result.active_definitions == 8
        assert result.platform_wide_definitions == 2
        assert "vessel" in result.by_entity_type

    @pytest.mark.asyncio
    async def test_bulk_operation_success(self, field_service, mock_db):
        """Test successful bulk operations."""
        field_ids = [uuid4(), uuid4(), uuid4()]
        operation = "deactivate"
        
        # Mock database operations
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        
        # Execute
        result = await field_service.bulk_operation(field_ids, operation)
        
        # Verify
        assert result["processed"] == 3
        assert result["failed"] == 0
        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_field_definition_model_methods(self, sample_field_definition):
        """Test field definition model helper methods."""
        # Test is_platform_wide
        sample_field_definition.tenant_id = None
        assert sample_field_definition.is_platform_wide() is True
        
        sample_field_definition.tenant_id = uuid4()
        assert sample_field_definition.is_platform_wide() is False
        
        # Test is_tenant_specific
        assert sample_field_definition.is_tenant_specific() is True
        
        sample_field_definition.tenant_id = None
        assert sample_field_definition.is_tenant_specific() is False
        
        # Test get_storage_info for dynamic field
        sample_field_definition.field_type = FieldType.PLATFORM_DYNAMIC.value
        storage_info = sample_field_definition.get_storage_info()
        assert storage_info["type"] == "json"
        assert storage_info["location"] == "custom_attributes"
        
        # Test get_storage_info for core field
        sample_field_definition.field_type = FieldType.CORE.value
        sample_field_definition.storage_column = "test_column"
        storage_info = sample_field_definition.get_storage_info()
        assert storage_info["type"] == "column"
        assert storage_info["location"] == "test_column"
        
        # Test full_field_path
        sample_field_definition.field_type = FieldType.PLATFORM_DYNAMIC.value
        sample_field_definition.field_name = "test_field"
        assert sample_field_definition.full_field_path == "custom_attributes.test_field"
        
        # Test validate_storage_configuration
        sample_field_definition.field_type = FieldType.CORE.value
        sample_field_definition.storage_column = "test_column"
        sample_field_definition.storage_path = None
        assert sample_field_definition.validate_storage_configuration() is True
        
        sample_field_definition.field_type = FieldType.PLATFORM_DYNAMIC.value
        sample_field_definition.storage_column = None
        sample_field_definition.storage_path = "custom_attributes.test"
        assert sample_field_definition.validate_storage_configuration() is True