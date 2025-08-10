from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime


class TerminologyConfig(BaseModel):
    """Base terminology configuration schema"""
    
    class Config:
        extra = "allow"  # Allow additional terminology fields
    
    # Core entity terms
    tenant: Optional[str] = Field(None, description="Term for tenant entity")
    sub_tenant: Optional[str] = Field(None, description="Term for sub-tenant entity") 
    user: Optional[str] = Field(None, description="Term for user entity")
    role: Optional[str] = Field(None, description="Term for role entity")
    permission: Optional[str] = Field(None, description="Term for permission entity")
    resource: Optional[str] = Field(None, description="Term for resource entity")
    group: Optional[str] = Field(None, description="Term for group entity")
    
    # Plural forms
    tenants: Optional[str] = Field(None, description="Plural form of tenant")
    sub_tenants: Optional[str] = Field(None, description="Plural form of sub-tenant")
    users: Optional[str] = Field(None, description="Plural form of user")
    roles: Optional[str] = Field(None, description="Plural form of role")
    permissions: Optional[str] = Field(None, description="Plural form of permission")
    resources: Optional[str] = Field(None, description="Plural form of resource")
    groups: Optional[str] = Field(None, description="Plural form of group")
    
    # Action terms
    create_tenant: Optional[str] = Field(None, description="Create tenant action label")
    create_sub_tenant: Optional[str] = Field(None, description="Create sub-tenant action label")
    create_user: Optional[str] = Field(None, description="Create user action label")
    create_role: Optional[str] = Field(None, description="Create role action label")
    create_group: Optional[str] = Field(None, description="Create group action label")
    
    # Management page terms  
    tenant_management: Optional[str] = Field(None, description="Tenant management page title")
    sub_tenant_management: Optional[str] = Field(None, description="Sub-tenant management page title")
    user_management: Optional[str] = Field(None, description="User management page title")
    role_management: Optional[str] = Field(None, description="Role management page title")
    permission_management: Optional[str] = Field(None, description="Permission management page title")
    group_management: Optional[str] = Field(None, description="Group management page title")
    
    # Dashboard terms
    dashboard: Optional[str] = Field(None, description="Dashboard page title")
    dashboard_title: Optional[str] = Field(None, description="Dashboard header title")
    welcome_message: Optional[str] = Field(None, description="Dashboard welcome message")
    admin_title: Optional[str] = Field(None, description="Administrator title")
    
    @validator('*', pre=True)
    def validate_string_fields(cls, v):
        """Ensure all terminology values are non-empty strings"""
        if v is not None and (not isinstance(v, str) or not v.strip()):
            raise ValueError("Terminology values must be non-empty strings")
        return v.strip() if isinstance(v, str) else v


class TerminologyUpdate(BaseModel):
    """Schema for updating tenant terminology"""
    
    terminology: Dict[str, str] = Field(..., description="Terminology key-value pairs")
    inherit_parent: bool = Field(True, description="Whether to inherit from parent tenant")
    apply_to_children: bool = Field(False, description="Whether to apply to child tenants")
    
    @validator('terminology')
    def validate_terminology_dict(cls, v):
        """Validate terminology dictionary"""
        if not v:
            raise ValueError("Terminology dictionary cannot be empty")
        
        for key, value in v.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("Terminology keys must be non-empty strings")
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Terminology values must be non-empty strings")
        
        return v


class TerminologyResponse(BaseModel):
    """Schema for terminology API responses"""
    
    tenant_id: UUID = Field(..., description="Tenant ID")
    tenant_name: str = Field(..., description="Tenant name")
    tenant_code: str = Field(..., description="Tenant code")
    terminology: Dict[str, str] = Field(..., description="Effective terminology")
    is_inherited: bool = Field(..., description="Whether terminology is inherited from parent")
    inherited_from: Optional[UUID] = Field(None, description="Parent tenant ID if inherited")
    local_config: Dict[str, str] = Field(..., description="Local terminology configuration")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")
    template_applied: Optional[str] = Field(None, description="Applied template name")
    
    class Config:
        from_attributes = True


class TerminologyValidation(BaseModel):
    """Schema for terminology validation results"""
    
    valid: bool = Field(..., description="Whether terminology is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    

class TerminologyTemplate(BaseModel):
    """Schema for industry terminology templates"""
    
    name: str = Field(..., description="Template name")
    display_name: str = Field(..., description="Template display name") 
    description: str = Field(..., description="Template description")
    industry: str = Field(..., description="Target industry")
    terminology: Dict[str, str] = Field(..., description="Template terminology")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "maritime",
                "display_name": "Maritime Industry",
                "description": "Terminology for maritime and shipping industry",
                "industry": "maritime",
                "terminology": {
                    "tenant": "Maritime Authority",
                    "sub_tenant": "Port Organization",
                    "user": "Maritime Stakeholder",
                    "role": "Stakeholder Type",
                    "permission": "Service Clearance"
                }
            }
        }


class TerminologyTemplateApplication(BaseModel):
    """Schema for applying terminology templates"""
    
    template_name: str = Field(..., description="Template to apply")
    customizations: Optional[Dict[str, str]] = Field(
        default_factory=dict, 
        description="Custom overrides for template terms"
    )
    apply_to_children: bool = Field(False, description="Apply to child tenants")
    
    @validator('customizations')
    def validate_customizations(cls, v):
        """Validate customizations dictionary"""
        if v:
            for key, value in v.items():
                if not isinstance(key, str) or not key.strip():
                    raise ValueError("Customization keys must be non-empty strings")
                if not isinstance(value, str) or not value.strip():
                    raise ValueError("Customization values must be non-empty strings")
        return v


class TerminologyBulkOperation(BaseModel):
    """Schema for bulk terminology operations"""
    
    tenant_ids: List[UUID] = Field(..., description="List of tenant IDs to update")
    terminology: Dict[str, str] = Field(..., description="Terminology to apply")
    operation: str = Field(..., description="Operation type: 'apply', 'reset', 'merge'")
    recursive: bool = Field(False, description="Apply recursively to children")
    
    @validator('operation')
    def validate_operation(cls, v):
        """Validate operation type"""
        allowed_operations = ['apply', 'reset', 'merge']
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of: {', '.join(allowed_operations)}")
        return v
    
    @validator('tenant_ids')
    def validate_tenant_ids(cls, v):
        """Validate tenant IDs list"""
        if not v:
            raise ValueError("At least one tenant ID must be provided")
        if len(v) > 100:
            raise ValueError("Cannot process more than 100 tenants at once")
        return v


class TerminologyStats(BaseModel):
    """Schema for terminology statistics"""
    
    total_tenants: int = Field(..., description="Total number of tenants")
    tenants_with_custom_terminology: int = Field(..., description="Tenants with custom terminology")
    tenants_inheriting: int = Field(..., description="Tenants inheriting terminology")
    most_common_terms: Dict[str, str] = Field(..., description="Most commonly customized terms")
    template_usage: Dict[str, int] = Field(..., description="Usage count by template")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_tenants": 150,
                "tenants_with_custom_terminology": 25, 
                "tenants_inheriting": 125,
                "most_common_terms": {
                    "tenant": "Authority/Organization",
                    "user": "Stakeholder/Professional"
                },
                "template_usage": {
                    "maritime": 8,
                    "healthcare": 12,
                    "finance": 5
                }
            }
        }


class TerminologyDiff(BaseModel):
    """Schema for terminology differences between tenants"""
    
    tenant_a_id: UUID = Field(..., description="First tenant ID")
    tenant_b_id: UUID = Field(..., description="Second tenant ID") 
    differences: Dict[str, Dict[str, str]] = Field(..., description="Term differences")
    common_terms: Dict[str, str] = Field(..., description="Terms that are the same")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tenant_a_id": "123e4567-e89b-12d3-a456-426614174000",
                "tenant_b_id": "123e4567-e89b-12d3-a456-426614174001", 
                "differences": {
                    "tenant": {
                        "tenant_a": "Maritime Authority",
                        "tenant_b": "Health System"
                    },
                    "user": {
                        "tenant_a": "Maritime Stakeholder", 
                        "tenant_b": "Healthcare Professional"
                    }
                },
                "common_terms": {
                    "role": "Role",
                    "permission": "Permission"
                }
            }
        }