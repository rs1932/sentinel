# Import all schemas for easy access
from .auth import *
from .tenant import *
from .user import *
from .role import *
from .group import *
from .field_definition import *
from .menu import *

__all__ = [
    # Auth schemas
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",

    # Tenant schemas
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantListResponse",

    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListResponse",

    # Role schemas
    "RoleCreate",
    "RoleUpdate",
    "RoleQuery",
    "RoleResponse",
    "RoleDetailResponse",
    "RoleListResponse",
    "UserRoleAssignmentCreate",
    "UserRoleAssignmentUpdate",
    "UserRoleAssignmentResponse",
    "BulkRoleAssignmentRequest",
    "BulkRoleAssignmentResponse",
    "RoleHierarchyResponse",
    "RoleValidationResponse",

    # Group schemas
    "GroupCreate",
    "GroupUpdate",
    "GroupQuery",
    "GroupResponse",
    "GroupDetailResponse",
    "GroupListResponse",
    "GroupUserAddRequest",
    "GroupRoleAssignRequest",

    # Field Definition schemas
    "FieldDefinitionCreateRequest",
    "FieldDefinitionCreate",
    "FieldDefinitionUpdate",
    "FieldDefinitionResponse",
    "FieldDefinitionDetailResponse",
    "FieldDefinitionListResponse",
    "FieldDefinitionQuery",
    "FieldPermissionCheck",
    "FieldPermissionResponse",
    
    # Menu schemas
    "MenuItemCreateRequest",
    "MenuItemCreate",
    "MenuItemUpdate",
    "MenuItemResponse",
    "MenuItemWithChildren",
    "UserMenuCustomizationCreate",
    "UserMenuCustomizationUpdate",
    "UserMenuCustomizationResponse",
    "MenuQuery",
    "MenuItemListResponse",
    "UserMenuResponse",
    "MenuCustomizationBatch",
    "MenuCustomizationBatchResponse",
    "MenuStatistics",
]