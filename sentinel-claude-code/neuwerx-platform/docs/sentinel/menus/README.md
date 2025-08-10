# Menu & Navigation System Documentation

> **Module 9**: Comprehensive documentation for the Sentinel platform's hierarchical menu and navigation system with RBAC integration.

## Overview

The Sentinel platform implements a sophisticated menu and navigation system that provides:

- **Hierarchical Navigation**: Multi-level menu structures with parent-child relationships
- **Tenant Isolation**: System-wide and tenant-specific menu items
- **RBAC Integration**: Permission-based menu visibility and access control
- **User Customization**: Personal menu preferences (hide/show, reordering)
- **Industry Specific**: Tailored navigation for different logistics industries

## Quick Reference

| Component | Description |
|-----------|-------------|
| **Database Tables** | `sentinel.menu_items`, `sentinel.user_menu_customizations` |
| **Models** | `MenuItem`, `UserMenuCustomization` |
| **Service** | `MenuService` |
| **API Endpoints** | `/api/v1/navigation/*` |
| **Key Features** | Hierarchical structure, RBAC integration, user customization |

## Documentation Structure

- [Architecture Overview](./architecture.md) - System design and component relationships
- [Database Schema](./database-schema.md) - Detailed table structures and relationships
- [RBAC Integration](./rbac-integration.md) - How menus integrate with role-based access control
- [API Reference](./api-reference.md) - Complete API endpoint documentation
- [User Flows](./user-flows.md) - Common user scenarios and workflows
- [Implementation Guide](./implementation.md) - Developer implementation details
- [Examples](./examples.md) - Code examples and usage patterns

## Key Features

### 🏗️ Hierarchical Structure
- Multi-level menu trees with unlimited depth
- Parent-child relationships with cascade operations
- Automatic ordering and display management

### 🏢 Multi-Tenancy
- **System-wide menus**: Available to all users (Dashboard, Administration)
- **Tenant-specific menus**: Isolated per organization (Maritime, AirCargo, etc.)
- **Industry customization**: Specialized navigation for different logistics sectors

### 🔐 RBAC Integration
- **Permission-based visibility**: Menus shown only to authorized users
- **Role-aware navigation**: Different menu structures per user role
- **Resource linking**: Menu items can be linked to specific resources

### 🎛️ User Customization
- **Personal preferences**: Users can hide/show menu items
- **Custom ordering**: Reorder menus according to workflow
- **Persistent settings**: Customizations saved per user

### 🚀 Performance & Scalability
- **Efficient queries**: Optimized database structure
- **Caching ready**: Designed for menu caching strategies
- **Batch operations**: Support for bulk menu operations

## Quick Start

### 1. Basic Menu Retrieval
```python
from src.services.menu_service import MenuService

# Get user's personalized menu
user_menu = await menu_service.get_user_menu(user_id)

# List all available menu items
menu_items = await menu_service.list_menu_items(
    tenant_id=tenant_id,
    include_system_wide=True
)
```

### 2. Menu Customization
```python
# Customize user's menu
customizations = [
    {
        "menu_item_id": "some-uuid",
        "is_hidden": True,
        "custom_order": 5
    }
]
result = await menu_service.customize_user_menu(user_id, customizations)
```

### 3. RBAC Integration
```python
# Menu items automatically respect user permissions
# Only shows menus the user has access to based on:
# - Required permissions on menu items
# - User's roles and groups
# - Tenant membership
```

## Database Tables

### Primary Tables

1. **`sentinel.menu_items`** - Core menu structure
2. **`sentinel.user_menu_customizations`** - User-specific preferences

### Related Tables (RBAC Integration)

- `sentinel.users` - User accounts and tenant membership
- `sentinel.tenants` - Tenant organizations
- `sentinel.resources` - Linkable system resources
- `sentinel.roles` - User roles for permission checking
- `sentinel.permissions` - Permission definitions

## Integration Points

### Frontend Integration
- RESTful API endpoints for menu retrieval
- Real-time menu updates via API
- User customization interfaces

### RBAC System
- Automatic permission checking
- Role-based menu filtering
- Tenant-aware menu selection

### Resource Management
- Menu items can link to system resources
- Resource-based access control
- Workflow integration points

## Security Considerations

- **Permission Validation**: All menu items respect RBAC permissions
- **Tenant Isolation**: Strict separation between tenant menus
- **Input Validation**: All menu operations include proper validation
- **Audit Trail**: Menu changes are logged for security auditing

## Performance Notes

- **Database Indexes**: Optimized for hierarchical queries
- **Query Optimization**: Efficient menu tree building
- **Caching Strategy**: Ready for Redis/memory caching
- **Batch Operations**: Minimal database round trips

## Support & Troubleshooting

- **Logging**: Comprehensive logging in `MenuService`
- **Error Handling**: Detailed error messages and codes
- **Validation**: Input validation with clear error messages
- **Testing**: Extensive test coverage for all scenarios

---

📚 **Next Steps**: Review the [Architecture Overview](./architecture.md) for detailed system design information.