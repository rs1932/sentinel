from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from ..models.tenant import Tenant
from ..utils.exceptions import NotFoundHTTPError


class TerminologyService:
    """Service for managing tenant terminology configuration and resolution"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # In-memory cache for performance optimization
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get_tenant(self, tenant_id: UUID) -> Tenant:
        """Get tenant by ID with error handling"""
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = result.scalar_one_or_none()
        
        if not tenant:
            raise NotFoundHTTPError(f"Tenant not found: {tenant_id}")
        
        return tenant
    
    async def get_terminology(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get effective terminology for a tenant with caching"""
        cache_key = str(tenant_id)
        
        # Check cache first
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Fetch from database
        tenant = await self.get_tenant(tenant_id)
        terminology_data = tenant.get_terminology_with_metadata()
        
        # Add tenant information
        terminology_data.update({
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "tenant_code": tenant.code
        })
        
        # Cache the result
        self._cache[cache_key] = terminology_data
        
        return terminology_data
    
    async def update_terminology(
        self, 
        tenant_id: UUID, 
        terminology: Dict[str, str],
        inherit_parent: bool = True,
        apply_to_children: bool = False
    ) -> Dict[str, Any]:
        """Update tenant terminology configuration"""
        tenant = await self.get_tenant(tenant_id)
        
        # Set terminology with metadata
        metadata = {
            "inherit_parent": inherit_parent,
            "updated_by": "api",  # Could be enhanced to track actual user
            "updated_at": datetime.utcnow().isoformat()
        }
        
        tenant.set_terminology_config(terminology, metadata)
        
        # Apply to children if requested
        if apply_to_children:
            tenant.apply_terminology_to_children(terminology, recursive=True)
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(tenant)
        
        # Invalidate cache for this tenant and children
        await self._invalidate_cache_hierarchy(tenant_id)
        
        return await self.get_terminology(tenant_id)
    
    async def reset_terminology(self, tenant_id: UUID) -> Dict[str, Any]:
        """Reset tenant terminology to inherit from parent"""
        tenant = await self.get_tenant(tenant_id)
        
        # Clear local terminology configuration
        tenant.clear_terminology_config()
        
        # Save changes
        await self.db.commit()
        await self.db.refresh(tenant)
        
        # Invalidate cache
        self._invalidate_cache(tenant_id)
        
        return await self.get_terminology(tenant_id)
    
    async def apply_to_children(
        self, 
        tenant_id: UUID, 
        terminology: Optional[Dict[str, str]] = None,
        recursive: bool = True
    ) -> List[UUID]:
        """Apply terminology configuration to all child tenants"""
        tenant = await self.get_tenant(tenant_id)
        
        # Use current effective terminology if none provided
        if terminology is None:
            terminology = tenant.get_effective_terminology()
        
        # Get all child tenant IDs using async queries
        affected_tenant_ids = []
        await self._collect_child_tenant_ids_async(tenant_id, affected_tenant_ids)
        
        # Apply terminology to each child tenant
        for child_id in affected_tenant_ids:
            child_tenant = await self.get_tenant(child_id)
            child_tenant.set_terminology_config(
                terminology,
                metadata={
                    "applied_from_parent": tenant_id,
                    "applied_at": datetime.utcnow().isoformat()
                }
            )
        
        # Save changes
        await self.db.commit()
        
        # Invalidate cache for all affected tenants
        for child_id in affected_tenant_ids:
            self._invalidate_cache(child_id)
        
        return affected_tenant_ids
    
    async def get_terminology_simple(self, tenant_id: UUID) -> Dict[str, str]:
        """Get just the effective terminology dictionary (no metadata)"""
        tenant = await self.get_tenant(tenant_id)
        return tenant.get_effective_terminology()
    
    def get_default_terminology(self) -> Dict[str, str]:
        """Get default Sentinel terminology"""
        # Create a temporary tenant instance to access default terminology
        temp_tenant = Tenant()
        return temp_tenant._get_default_terminology()
    
    async def validate_terminology(self, terminology: Dict[str, str]) -> Dict[str, Any]:
        """Validate terminology configuration"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check for required terminology keys
        default_terminology = self.get_default_terminology()
        core_keys = [
            "tenant", "sub_tenant", "user", "role", 
            "permission", "resource", "group"
        ]
        
        for key in core_keys:
            if key not in terminology:
                validation_result["warnings"].append(
                    f"Missing core terminology key: '{key}'. Will use default: '{default_terminology.get(key)}'"
                )
        
        # Check for empty values
        for key, value in terminology.items():
            if not value or not value.strip():
                validation_result["errors"].append(f"Empty value for terminology key: '{key}'")
                validation_result["valid"] = False
        
        # Check for extremely long values
        for key, value in terminology.items():
            if len(value) > 100:
                validation_result["warnings"].append(
                    f"Very long terminology value for '{key}': {len(value)} characters"
                )
        
        return validation_result
    
    # =====================================================
    # CACHE MANAGEMENT
    # =====================================================
    
    def _invalidate_cache(self, tenant_id: UUID) -> None:
        """Invalidate cache for a specific tenant"""
        cache_key = str(tenant_id)
        if cache_key in self._cache:
            del self._cache[cache_key]
    
    async def _invalidate_cache_hierarchy(self, tenant_id: UUID) -> None:
        """Invalidate cache for tenant and all its children"""
        # Invalidate current tenant
        self._invalidate_cache(tenant_id)
        
        # Query for all child tenants to avoid lazy loading issues
        from sqlalchemy import select
        result = await self.db.execute(
            select(Tenant.id).where(Tenant.parent_tenant_id == tenant_id)
        )
        child_ids = [row[0] for row in result.fetchall()]
        
        # Recursively invalidate children
        for child_id in child_ids:
            self._invalidate_cache(child_id)
            # Recursively invalidate grandchildren
            await self._invalidate_cache_hierarchy(child_id)
    
    async def _collect_child_tenant_ids_async(self, tenant_id: UUID, result: List[UUID]) -> None:
        """Recursively collect all child tenant IDs using async queries"""
        from sqlalchemy import select
        query_result = await self.db.execute(
            select(Tenant.id).where(Tenant.parent_tenant_id == tenant_id)
        )
        child_ids = [row[0] for row in query_result.fetchall()]
        
        for child_id in child_ids:
            result.append(child_id)
            await self._collect_child_tenant_ids_async(child_id, result)
    
    def clear_cache(self) -> None:
        """Clear entire terminology cache"""
        self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        return {
            "cached_tenants": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "memory_usage_estimate": sum(
                len(str(data)) for data in self._cache.values()
            )
        }
    
    # =====================================================
    # INDUSTRY TEMPLATES (Future Enhancement)
    # =====================================================
    
    def get_industry_templates(self) -> Dict[str, Dict[str, str]]:
        """Get available industry terminology templates (placeholder)"""
        # This will be implemented in a future phase
        return {
            "maritime": {
                "tenant": "Maritime Authority",
                "sub_tenant": "Port Organization",
                "user": "Maritime Stakeholder",
                "role": "Stakeholder Type",
                "permission": "Service Clearance"
            },
            "healthcare": {
                "tenant": "Health System", 
                "sub_tenant": "Hospital",
                "user": "Healthcare Professional",
                "role": "Clinical Role",
                "permission": "Clinical Access"
            },
            "finance": {
                "tenant": "Financial Institution",
                "sub_tenant": "Branch",
                "user": "Employee",
                "role": "Position",
                "permission": "Transaction Authority"
            }
        }
    
    async def apply_template(
        self, 
        tenant_id: UUID, 
        template_name: str, 
        customizations: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Apply an industry template with optional customizations (placeholder)"""
        templates = self.get_industry_templates()
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        # Start with template
        terminology = templates[template_name].copy()
        
        # Apply customizations
        if customizations:
            terminology.update(customizations)
        
        # Update tenant
        return await self.update_terminology(
            tenant_id, 
            terminology,
            inherit_parent=False  # Templates override inheritance
        )