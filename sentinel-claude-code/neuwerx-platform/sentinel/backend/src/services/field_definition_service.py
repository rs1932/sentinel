"""
FieldDefinitionService for Module 8: Field Definition management
"""
from typing import List, Optional, Dict
from uuid import UUID as UUID_T
from sqlalchemy import select, and_, or_, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import FieldDefinition, FieldType, FieldPermission, Tenant
from src.schemas.field_definition import (
    FieldDefinitionCreate, FieldDefinitionUpdate, FieldDefinitionResponse,
    FieldDefinitionDetailResponse, FieldDefinitionQuery, FieldDefinitionListResponse,
    FieldDefinitionStatistics, FieldPermissionResponse
)
from src.core.exceptions import NotFoundError, ConflictError, ValidationError


class FieldDefinitionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_field_definition(self, field_data: FieldDefinitionCreate) -> FieldDefinitionResponse:
        """Create a new field definition with validation."""

        # Check if field definition already exists
        query = select(FieldDefinition).where(
            and_(
                FieldDefinition.entity_type == field_data.entity_type,
                FieldDefinition.field_name == field_data.field_name,
                FieldDefinition.tenant_id == field_data.tenant_id
            )
        )
        existing_definition = await self.db.execute(query)
        if existing_definition.scalar_one_or_none():
            raise ConflictError(
                f"Field definition '{field_data.field_name}' already exists "
                f"for entity type '{field_data.entity_type}'"
            )

        # Validate tenant exists if tenant_id is provided
        if field_data.tenant_id:
            tenant_result = await self.db.execute(
                select(Tenant).where(Tenant.id == field_data.tenant_id)
            )
            if not tenant_result.scalar_one_or_none():
                raise NotFoundError(f"Tenant with ID {field_data.tenant_id} not found")

        # Validate storage configuration
        if field_data.field_type == FieldType.CORE.value:
            if not field_data.storage_column:
                raise ValidationError("storage_column is required for core fields")
            if field_data.storage_path:
                raise ValidationError("storage_path should not be set for core fields")
        else:  # platform_dynamic or tenant_specific
            if not field_data.storage_path:
                raise ValidationError("storage_path is required for dynamic fields")
            if field_data.storage_column:
                raise ValidationError("storage_column should not be set for dynamic fields")

        # Create field definition
        field_definition = FieldDefinition(
            tenant_id=field_data.tenant_id,
            entity_type=field_data.entity_type,
            field_name=field_data.field_name,
            field_type=field_data.field_type,
            data_type=field_data.data_type,
            storage_column=field_data.storage_column,
            storage_path=field_data.storage_path,
            display_name=field_data.display_name,
            description=field_data.description,
            validation_rules=field_data.validation_rules,
            default_visibility=field_data.default_visibility,
            is_indexed=field_data.is_indexed,
            is_required=field_data.is_required,
            is_active=field_data.is_active
        )

        self.db.add(field_definition)
        await self.db.commit()
        await self.db.refresh(field_definition)

        return FieldDefinitionResponse.model_validate(field_definition)

    async def get_field_definition(self, field_id: UUID_T) -> FieldDefinitionDetailResponse:
        """Get field definition by ID with detailed information."""

        query = select(FieldDefinition).where(FieldDefinition.id == field_id)
        result = await self.db.execute(query)
        field_definition = result.scalar_one_or_none()

        if not field_definition:
            raise NotFoundError(f"Field definition with ID {field_id} not found")

        # Create detailed response
        base_response = FieldDefinitionResponse.model_validate(field_definition)

        return FieldDefinitionDetailResponse(
            **base_response.model_dump(),
            is_platform_wide=field_definition.is_platform_wide(),
            full_field_path=field_definition.full_field_path,
            storage_info=field_definition.get_storage_info()
        )

    async def list_field_definitions(
        self,
        query_params: FieldDefinitionQuery,
        tenant_id: Optional[UUID_T] = None
    ) -> FieldDefinitionListResponse:
        """List field definitions with filtering and pagination."""

        # Build base query
        query = select(FieldDefinition)
        where_conditions = [FieldDefinition.is_active.is_(True)]

        # Apply filters
        if query_params.entity_type:
            where_conditions.append(FieldDefinition.entity_type == query_params.entity_type)

        if query_params.field_type:
            where_conditions.append(FieldDefinition.field_type == query_params.field_type)

        if query_params.tenant_id:
            where_conditions.append(FieldDefinition.tenant_id == query_params.tenant_id)
        elif tenant_id:
            # Include both platform-wide and tenant-specific fields
            where_conditions.append(
                or_(
                    FieldDefinition.tenant_id.is_(None),
                    FieldDefinition.tenant_id == tenant_id
                )
            )

        if query_params.is_active is not None:
            where_conditions[0] = FieldDefinition.is_active == query_params.is_active

        if query_params.search:
            search_term = f"%{query_params.search.lower()}%"
            where_conditions.append(
                or_(
                    func.lower(FieldDefinition.field_name).like(search_term),
                    func.lower(FieldDefinition.display_name).like(search_term),
                    func.lower(FieldDefinition.description).like(search_term)
                )
            )

        query = query.where(and_(*where_conditions))

        # Count total items
        count_query = select(func.count()).select_from(query.alias())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting
        sort_column = getattr(FieldDefinition, query_params.sort_by, FieldDefinition.field_name)
        if query_params.sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (query_params.page - 1) * query_params.limit
        query = query.offset(offset).limit(query_params.limit)

        # Execute query
        result = await self.db.execute(query)
        field_definitions = result.scalars().all()

        # Convert to response schemas
        items = [FieldDefinitionResponse.model_validate(fd) for fd in field_definitions]

        return FieldDefinitionListResponse(
            items=items,
            total=total,
            page=query_params.page,
            limit=query_params.limit,
            has_next=offset + len(items) < total,
            has_prev=query_params.page > 1
        )

    async def update_field_definition(
        self,
        field_id: UUID_T,
        field_data: FieldDefinitionUpdate
    ) -> FieldDefinitionResponse:
        """Update field definition."""

        # Get existing field definition
        query = select(FieldDefinition).where(FieldDefinition.id == field_id)
        result = await self.db.execute(query)
        field_definition = result.scalar_one_or_none()

        if not field_definition:
            raise NotFoundError(f"Field definition with ID {field_id} not found")

        # Update fields
        update_data = field_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(field_definition, field, value)

        await self.db.commit()
        await self.db.refresh(field_definition)

        return FieldDefinitionResponse.model_validate(field_definition)

    async def delete_field_definition(self, field_id: UUID_T) -> bool:
        """Soft delete field definition by marking as inactive."""

        query = select(FieldDefinition).where(FieldDefinition.id == field_id)
        result = await self.db.execute(query)
        field_definition = result.scalar_one_or_none()

        if not field_definition:
            raise NotFoundError(f"Field definition with ID {field_id} not found")

        field_definition.is_active = False
        await self.db.commit()

        return True

    async def get_field_definitions_by_entity(
        self,
        entity_type: str,
        tenant_id: Optional[UUID_T] = None
    ) -> List[FieldDefinitionResponse]:
        """Get all field definitions for a specific entity type."""

        where_conditions = [
            FieldDefinition.entity_type == entity_type,
            FieldDefinition.is_active.is_(True)
        ]

        if tenant_id:
            # Include both platform-wide and tenant-specific fields
            where_conditions.append(
                or_(
                    FieldDefinition.tenant_id.is_(None),
                    FieldDefinition.tenant_id == tenant_id
                )
            )

        query = select(FieldDefinition).where(and_(*where_conditions))
        query = query.order_by(FieldDefinition.field_name)

        result = await self.db.execute(query)
        field_definitions = result.scalars().all()

        return [FieldDefinitionResponse.model_validate(fd) for fd in field_definitions]

    async def check_field_permissions(
        self,
        user_id: UUID_T,
        entity_type: str,
        entity_id: Optional[str] = None,
        fields: Optional[List[str]] = None
    ) -> FieldPermissionResponse:
        """Check field permissions for a user."""
        # This is a placeholder implementation
        # In a real implementation, you would check against the permission system

        # Get field definitions for the entity type
        field_definitions = await self.get_field_definitions_by_entity(entity_type)

        # If specific fields are requested, filter to those
        if fields:
            field_definitions = [fd for fd in field_definitions if fd.field_name in fields]
            checked_fields = fields
        else:
            checked_fields = [fd.field_name for fd in field_definitions]

        # Build field permissions based on default visibility
        # In a real implementation, this would check actual user permissions
        field_permissions = {}
        for fd in field_definitions:
            if fd.default_visibility == FieldPermission.READ.value:
                field_permissions[fd.field_name] = ["read"]
            elif fd.default_visibility == FieldPermission.WRITE.value:
                field_permissions[fd.field_name] = ["read", "write"]
            else:  # hidden
                field_permissions[fd.field_name] = []

        return FieldPermissionResponse(
            field_permissions=field_permissions,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            checked_fields=checked_fields
        )

    async def get_statistics(self, tenant_id: Optional[UUID_T] = None) -> FieldDefinitionStatistics:
        """Get field definition statistics."""

        where_conditions = []
        if tenant_id:
            where_conditions.append(
                or_(
                    FieldDefinition.tenant_id.is_(None),
                    FieldDefinition.tenant_id == tenant_id
                )
            )

        base_query = select(FieldDefinition)
        if where_conditions:
            base_query = base_query.where(and_(*where_conditions))

        # Total definitions
        total_result = await self.db.execute(
            select(func.count()).select_from(base_query.alias())
        )
        total_definitions = total_result.scalar()

        # Active/inactive definitions
        active_result = await self.db.execute(
            base_query.where(FieldDefinition.is_active.is_(True))
            .statement.with_only_columns([func.count()])
        )
        active_definitions = active_result.scalar()
        inactive_definitions = total_definitions - active_definitions

        # Platform-wide vs tenant-specific
        platform_result = await self.db.execute(
            base_query.where(FieldDefinition.tenant_id.is_(None)).statement.with_only_columns([func.count()])
        )
        platform_wide_definitions = platform_result.scalar()
        tenant_specific_definitions = total_definitions - platform_wide_definitions

        # By entity type
        entity_type_result = await self.db.execute(
            base_query.statement.with_only_columns([
                FieldDefinition.entity_type,
                func.count().label('count')
            ]).group_by(FieldDefinition.entity_type)
        )
        by_entity_type = {row.entity_type: row.count for row in entity_type_result.fetchall()}

        # By field type
        field_type_result = await self.db.execute(
            base_query.statement.with_only_columns([
                FieldDefinition.field_type,
                func.count().label('count')
            ]).group_by(FieldDefinition.field_type)
        )
        by_field_type = {row.field_type: row.count for row in field_type_result.fetchall()}

        # By data type
        data_type_result = await self.db.execute(
            base_query.statement.with_only_columns([
                FieldDefinition.data_type,
                func.count().label('count')
            ]).group_by(FieldDefinition.data_type)
        )
        by_data_type = {row.data_type: row.count for row in data_type_result.fetchall()}

        return FieldDefinitionStatistics(
            total_definitions=total_definitions,
            by_entity_type=by_entity_type,
            by_field_type=by_field_type,
            by_data_type=by_data_type,
            active_definitions=active_definitions,
            inactive_definitions=inactive_definitions,
            platform_wide_definitions=platform_wide_definitions,
            tenant_specific_definitions=tenant_specific_definitions
        )

    async def bulk_operation(
        self,
        field_definition_ids: List[UUID_T],
        operation: str
    ) -> Dict[str, int]:
        """Perform bulk operations on field definitions."""

        processed = 0
        failed = 0

        for field_id in field_definition_ids:
            try:
                if operation == "activate":
                    await self.db.execute(
                        update(FieldDefinition)
                        .where(FieldDefinition.id == field_id)
                        .values(is_active=True)
                    )
                elif operation == "deactivate":
                    await self.db.execute(
                        update(FieldDefinition)
                        .where(FieldDefinition.id == field_id)
                        .values(is_active=False)
                    )
                elif operation == "delete":
                    await self.db.execute(
                        delete(FieldDefinition)
                        .where(FieldDefinition.id == field_id)
                    )
                processed += 1
            except Exception:
                failed += 1

        await self.db.commit()

        return {
            "processed": processed,
            "failed": failed
        }
