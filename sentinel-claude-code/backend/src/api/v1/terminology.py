from fastapi import APIRouter, Depends, status, Query
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.services.terminology_service import TerminologyService
from src.core.security_utils import get_current_user, require_scopes, CurrentUser
from src.schemas.terminology import (
    TerminologyResponse, 
    TerminologyUpdate, 
    TerminologyValidation,
    TerminologyTemplate,
    TerminologyTemplateApplication,
    TerminologyBulkOperation,
    TerminologyStats
)
from src.utils.exceptions import (
    NotFoundHTTPError, 
    BadRequestError, 
    ConflictHTTPError
)

router = APIRouter(prefix="/terminology", tags=["Terminology"])


@router.get(
    "/tenants/{tenant_id}",
    response_model=TerminologyResponse,
    summary="Get tenant terminology",
    description="Get effective terminology configuration for a tenant with inheritance"
)
async def get_tenant_terminology(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("tenant:read")),
    db: AsyncSession = Depends(get_db)
):
    """Get effective terminology configuration for a tenant"""
    try:
        service = TerminologyService(db)
        return await service.get_terminology(tenant_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))


@router.put(
    "/tenants/{tenant_id}",
    response_model=TerminologyResponse,
    summary="Update tenant terminology", 
    description="Update terminology configuration for a tenant"
)
async def update_tenant_terminology(
    tenant_id: UUID,
    terminology_data: TerminologyUpdate,
    current_user: CurrentUser = Depends(require_scopes("tenant:write")),
    db: AsyncSession = Depends(get_db)
):
    """Update terminology configuration for a tenant"""
    try:
        service = TerminologyService(db)
        
        # Validate terminology first
        validation = await service.validate_terminology(terminology_data.terminology)
        if not validation["valid"]:
            raise BadRequestError(f"Invalid terminology: {validation['errors']}")
        
        return await service.update_terminology(
            tenant_id,
            terminology_data.terminology,
            terminology_data.inherit_parent,
            terminology_data.apply_to_children
        )
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))


@router.delete(
    "/tenants/{tenant_id}",
    response_model=TerminologyResponse,
    summary="Reset tenant terminology",
    description="Reset tenant terminology to inherit from parent (clear local configuration)"
)
async def reset_tenant_terminology(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("tenant:write")),
    db: AsyncSession = Depends(get_db)
):
    """Reset tenant terminology to inherit from parent"""
    try:
        service = TerminologyService(db)
        return await service.reset_terminology(tenant_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))


@router.post(
    "/tenants/{tenant_id}/apply-to-children",
    summary="Apply terminology to children",
    description="Apply tenant's terminology configuration to all child tenants"
)
async def apply_terminology_to_children(
    tenant_id: UUID,
    recursive: bool = Query(True, description="Apply recursively to all descendants"),
    current_user: CurrentUser = Depends(require_scopes("tenant:admin")),
    db: AsyncSession = Depends(get_db)
):
    """Apply tenant terminology to all child tenants"""
    try:
        service = TerminologyService(db)
        affected_tenant_ids = await service.apply_to_children(
            tenant_id, 
            recursive=recursive
        )
        
        return {
            "message": f"Terminology applied to {len(affected_tenant_ids)} child tenants",
            "affected_tenant_ids": affected_tenant_ids,
            "recursive": recursive
        }
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))


@router.post(
    "/tenants/{tenant_id}/validate",
    response_model=TerminologyValidation,
    summary="Validate terminology",
    description="Validate terminology configuration without saving"
)
async def validate_terminology(
    tenant_id: UUID,
    terminology: Dict[str, str],
    current_user: CurrentUser = Depends(require_scopes("tenant:read")),
    db: AsyncSession = Depends(get_db)
):
    """Validate terminology configuration"""
    try:
        service = TerminologyService(db)
        return await service.validate_terminology(terminology)
    except Exception as e:
        raise BadRequestError(str(e))


@router.get(
    "/defaults",
    response_model=Dict[str, str],
    summary="Get default terminology",
    description="Get default Sentinel terminology configuration"
)
async def get_default_terminology(
    current_user: CurrentUser = Depends(require_scopes("tenant:read")),
    db: AsyncSession = Depends(get_db)
):
    """Get default Sentinel terminology"""
    service = TerminologyService(db)
    return service.get_default_terminology()


# =====================================================
# TEMPLATE MANAGEMENT (Future Enhancement)
# =====================================================

@router.get(
    "/templates",
    response_model=Dict[str, TerminologyTemplate],
    summary="Get terminology templates",
    description="Get available industry terminology templates"
)
async def get_terminology_templates(
    current_user: CurrentUser = Depends(require_scopes("tenant:read")),
    db: AsyncSession = Depends(get_db)
):
    """Get available terminology templates"""
    service = TerminologyService(db)
    templates_data = service.get_industry_templates()
    
    # Convert to proper template format
    templates = {}
    for name, terminology in templates_data.items():
        templates[name] = TerminologyTemplate(
            name=name,
            display_name=name.title() + " Industry",
            description=f"Terminology template for {name} industry",
            industry=name,
            terminology=terminology
        )
    
    return templates


@router.post(
    "/tenants/{tenant_id}/apply-template",
    response_model=TerminologyResponse,
    summary="Apply terminology template",
    description="Apply an industry terminology template to a tenant"
)
async def apply_terminology_template(
    tenant_id: UUID,
    template_data: TerminologyTemplateApplication,
    current_user: CurrentUser = Depends(require_scopes("tenant:write")),
    db: AsyncSession = Depends(get_db)
):
    """Apply an industry terminology template"""
    try:
        service = TerminologyService(db)
        return await service.apply_template(
            tenant_id,
            template_data.template_name,
            template_data.customizations
        )
    except ValueError as e:
        raise BadRequestError(str(e))
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))


# =====================================================
# BULK OPERATIONS
# =====================================================

@router.post(
    "/bulk-operation", 
    summary="Bulk terminology operation",
    description="Apply terminology operations to multiple tenants"
)
async def bulk_terminology_operation(
    operation_data: TerminologyBulkOperation,
    current_user: CurrentUser = Depends(require_scopes("tenant:admin")),
    db: AsyncSession = Depends(get_db)
):
    """Perform bulk terminology operations"""
    try:
        service = TerminologyService(db)
        results = []
        
        for tenant_id in operation_data.tenant_ids:
            try:
                if operation_data.operation == "apply":
                    result = await service.update_terminology(
                        tenant_id,
                        operation_data.terminology,
                        apply_to_children=operation_data.recursive
                    )
                elif operation_data.operation == "reset":
                    result = await service.reset_terminology(tenant_id)
                elif operation_data.operation == "merge":
                    # Get current terminology and merge with new
                    current = await service.get_terminology_simple(tenant_id)
                    merged = {**current, **operation_data.terminology}
                    result = await service.update_terminology(tenant_id, merged)
                
                results.append({
                    "tenant_id": tenant_id,
                    "status": "success",
                    "result": result
                })
                
            except Exception as e:
                results.append({
                    "tenant_id": tenant_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "operation": operation_data.operation,
            "total_tenants": len(operation_data.tenant_ids),
            "successful": len([r for r in results if r["status"] == "success"]),
            "failed": len([r for r in results if r["status"] == "error"]),
            "results": results
        }
        
    except Exception as e:
        raise BadRequestError(str(e))


# =====================================================
# ANALYTICS & MONITORING
# =====================================================

@router.get(
    "/cache-stats",
    summary="Get cache statistics",
    description="Get terminology cache statistics for monitoring"
)
async def get_terminology_cache_stats(
    current_user: CurrentUser = Depends(require_scopes("system:admin")),
    db: AsyncSession = Depends(get_db)
):
    """Get cache statistics"""
    service = TerminologyService(db)
    return service.get_cache_stats()


@router.post(
    "/clear-cache",
    summary="Clear terminology cache",
    description="Clear the terminology cache (admin operation)"
)
async def clear_terminology_cache(
    current_user: CurrentUser = Depends(require_scopes("system:admin")),
    db: AsyncSession = Depends(get_db)
):
    """Clear terminology cache"""
    service = TerminologyService(db)
    service.clear_cache()
    
    return {"message": "Terminology cache cleared successfully"}


# =====================================================
# UTILITY ENDPOINTS
# =====================================================

@router.get(
    "/tenants/{tenant_id}/simple",
    response_model=Dict[str, str],
    summary="Get simple terminology",
    description="Get just the effective terminology dictionary (no metadata)"
)
async def get_simple_terminology(
    tenant_id: UUID,
    current_user: CurrentUser = Depends(require_scopes("tenant:read")),
    db: AsyncSession = Depends(get_db)
):
    """Get simple terminology dictionary"""
    try:
        service = TerminologyService(db)
        return await service.get_terminology_simple(tenant_id)
    except Exception as e:
        if "not found" in str(e).lower():
            raise NotFoundHTTPError(str(e))
        raise BadRequestError(str(e))