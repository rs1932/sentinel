# Menu System Architecture

> Comprehensive architectural overview of the Menu & Navigation system

## System Overview

The Sentinel Menu & Navigation system is designed as a hierarchical, multi-tenant, permission-aware navigation framework that provides personalized menu experiences for users across different logistics industry verticals.

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Frontend]
        MOBILE[Mobile App]
        API_CLIENT[API Clients]
    end

    subgraph "API Layer"
        REST[REST API Endpoints]
        AUTH[Authentication]
        VALIDATION[Request Validation]
    end

    subgraph "Business Logic Layer"
        MENU_SERVICE[MenuService]
        PERMISSION_SERVICE[PermissionService]
        USER_SERVICE[UserService]
        TENANT_SERVICE[TenantService]
    end

    subgraph "Data Access Layer"
        MODELS[SQLAlchemy Models]
        DATABASE[(PostgreSQL)]
    end

    subgraph "External Systems"
        RBAC[RBAC System]
        AUDIT[Audit Logging]
        CACHE[Redis Cache]
    end

    WEB --> REST
    MOBILE --> REST
    API_CLIENT --> REST

    REST --> AUTH
    REST --> VALIDATION
    REST --> MENU_SERVICE

    MENU_SERVICE --> PERMISSION_SERVICE
    MENU_SERVICE --> USER_SERVICE
    MENU_SERVICE --> TENANT_SERVICE
    MENU_SERVICE --> MODELS

    MODELS --> DATABASE

    MENU_SERVICE --> RBAC
    MENU_SERVICE --> AUDIT
    MENU_SERVICE --> CACHE

    classDef clientStyle fill:#e3f2fd
    classDef apiStyle fill:#f3e5f5
    classDef businessStyle fill:#e8f5e8
    classDef dataStyle fill:#fff3e0
    classDef externalStyle fill:#fce4ec

    class WEB,MOBILE,API_CLIENT clientStyle
    class REST,AUTH,VALIDATION apiStyle
    class MENU_SERVICE,PERMISSION_SERVICE,USER_SERVICE,TENANT_SERVICE businessStyle
    class MODELS,DATABASE dataStyle
    class RBAC,AUDIT,CACHE externalStyle
```

## Core Components

### 1. MenuService (Business Logic Core)

**Purpose**: Central orchestrator for all menu operations

**Key Responsibilities**:
- Menu CRUD operations
- Hierarchical menu building
- Permission-based filtering
- User customization application
- Statistical reporting

```python
class MenuService:
    """Core service for menu operations."""
    
    async def get_user_menu(self, user_id: UUID) -> UserMenuResponse:
        """Build personalized hierarchical menu for user."""
    
    async def create_menu_item(self, item_data: MenuItemCreate) -> MenuItemResponse:
        """Create new menu item with validation."""
    
    async def customize_user_menu(self, user_id: UUID, customizations: List[Dict]) -> Dict:
        """Apply user-specific menu customizations."""
```

### 2. Data Models (SQLAlchemy ORM)

**MenuItem Model**: Hierarchical menu structure
```python
class MenuItem(BaseModel):
    # Hierarchy
    parent_id: Optional[UUID]
    children: List["MenuItem"]
    
    # Identity
    name: str
    display_name: Optional[str]
    
    # Tenant isolation
    tenant_id: Optional[UUID]
    
    # RBAC integration
    required_permission: Optional[str]
    resource_id: Optional[UUID]
    
    # Display properties
    icon: Optional[str]
    url: Optional[str]
    display_order: int
    is_visible: bool
    menu_metadata: Dict[str, Any]
```

**UserMenuCustomization Model**: User preferences
```python
class UserMenuCustomization(BaseModel):
    user_id: UUID
    menu_item_id: UUID
    is_hidden: bool
    custom_order: Optional[int]
```

### 3. API Layer (FastAPI)

**Endpoints Structure**:
```
/api/v1/navigation/
├── GET    /menu                    # Get user's personalized menu
├── POST   /customize               # Customize user menu
├── GET    /menu-items             # List all menu items (admin)
├── POST   /menu-items             # Create menu item (admin)
├── GET    /menu-items/{id}        # Get menu item details
├── PATCH  /menu-items/{id}        # Update menu item (admin)
├── DELETE /menu-items/{id}        # Delete menu item (admin)
├── GET    /statistics             # Menu statistics
├── GET    /customizations/{id}    # Get user customization
└── DELETE /customizations/{id}    # Reset user customization
```

## Data Flow Architecture

### 1. Menu Retrieval Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as API Layer
    participant MS as MenuService
    participant PS as PermissionService
    participant DB as Database
    participant Cache as Redis Cache

    U->>API: GET /navigation/menu
    API->>API: Authenticate user
    API->>MS: get_user_menu(user_id)
    
    MS->>Cache: Check cached menu
    alt Cache Hit
        Cache-->>MS: Return cached menu
    else Cache Miss
        MS->>DB: Get menu items for user tenant
        DB-->>MS: Raw menu items
        MS->>PS: Get user permissions
        PS-->>MS: Permission list
        MS->>MS: Filter menus by permissions
        MS->>DB: Get user customizations
        DB-->>MS: Customizations
        MS->>MS: Apply customizations
        MS->>MS: Build hierarchy
        MS->>Cache: Cache result
    end
    
    MS-->>API: UserMenuResponse
    API-->>U: JSON menu structure
```

### 2. Menu Creation Flow

```mermaid
sequenceDiagram
    participant Admin as Admin User
    participant API as API Layer  
    participant MS as MenuService
    participant Val as Validator
    participant DB as Database
    participant Audit as Audit Log

    Admin->>API: POST /navigation/menu-items
    API->>API: Validate admin permissions
    API->>Val: Validate menu item data
    Val-->>API: Validation result
    API->>MS: create_menu_item(data)
    
    MS->>MS: Check for duplicates
    MS->>MS: Validate parent exists
    MS->>MS: Validate tenant access
    MS->>DB: Insert menu item
    DB-->>MS: Created menu item
    MS->>Audit: Log menu creation
    MS-->>API: MenuItemResponse
    API-->>Admin: Created menu item
```

## Multi-Tenancy Architecture

### 1. Tenant Isolation Model

```mermaid
graph TD
    subgraph "System-wide Menus (tenant_id = NULL)"
        SYS1[Dashboard]
        SYS2[Administration]
        SYS3[User Management]
        SYS4[System Reports]
    end

    subgraph "Maritime Tenant (MARITIME)"
        MAR1[Port Operations]
        MAR2[Vessel Management]
        MAR3[Cargo Manifest]
        MAR4[Customs Clearance]
        MAR5[Port Security]
    end

    subgraph "Air Cargo Tenant (AIRCARGO)"
        AIR1[Flight Coordination]
        AIR2[Cargo Handling]
        AIR3[Freight Management]
        AIR4[Security Screening]
    end

    subgraph "Ground Logistics (GROUNDLINK)"
        GRD1[Warehouse Operations]
        GRD2[Fleet Management]
        GRD3[Route Optimization]
        GRD4[Inventory Control]
    end

    subgraph "User Views"
        MAR_USER[Maritime User Sees]
        AIR_USER[Air Cargo User Sees]
        GRD_USER[Ground User Sees]
    end

    SYS1 --> MAR_USER
    SYS1 --> AIR_USER
    SYS1 --> GRD_USER

    MAR1 --> MAR_USER
    MAR2 --> MAR_USER

    AIR1 --> AIR_USER
    AIR2 --> AIR_USER

    GRD1 --> GRD_USER
    GRD2 --> GRD_USER
```

### 2. Menu Resolution Logic

```python
def resolve_user_menus(user: User) -> List[MenuItem]:
    """Resolve menus visible to a user based on tenant membership."""
    
    # 1. Get system-wide menus (available to all users)
    system_menus = get_system_wide_menus()
    
    # 2. Get tenant-specific menus  
    tenant_menus = get_tenant_menus(user.tenant_id) if user.tenant_id else []
    
    # 3. Combine and sort
    all_menus = system_menus + tenant_menus
    
    # 4. Filter by permissions
    accessible_menus = filter_by_permissions(all_menus, user)
    
    return accessible_menus
```

## Permission Integration Architecture

### 1. Permission Check Flow

```mermaid
flowchart TD
    START[Menu Item Request]
    CHECK_PERM{Has Required Permission?}
    CHECK_RESOURCE{Linked to Resource?}
    CHECK_RESOURCE_PERM{Has Resource Permission?}
    ALLOW[Show Menu Item]
    DENY[Hide Menu Item]
    
    START --> CHECK_PERM
    CHECK_PERM -->|No Perm Required| ALLOW
    CHECK_PERM -->|Has Permission| CHECK_RESOURCE
    CHECK_PERM -->|Missing Permission| DENY
    CHECK_RESOURCE -->|No Resource Link| ALLOW
    CHECK_RESOURCE -->|Has Resource Link| CHECK_RESOURCE_PERM
    CHECK_RESOURCE_PERM -->|Has Resource Perm| ALLOW
    CHECK_RESOURCE_PERM -->|Missing Resource Perm| DENY
```

### 2. Permission Hierarchy

```mermaid
graph TD
    subgraph "Permission Levels"
        GLOBAL[Global Permissions]
        TENANT[Tenant Permissions] 
        RESOURCE[Resource Permissions]
        INHERITED[Inherited Permissions]
    end

    subgraph "Assignment Sources"
        DIRECT[Direct Assignment]
        ROLE[Role Assignment]
        GROUP[Group Assignment]
    end

    subgraph "Menu Visibility"
        VISIBLE[Menu Visible]
        HIDDEN[Menu Hidden]
    end

    GLOBAL --> VISIBLE
    TENANT --> VISIBLE
    RESOURCE --> VISIBLE
    INHERITED --> VISIBLE

    DIRECT --> GLOBAL
    ROLE --> TENANT
    GROUP --> INHERITED

    VISIBLE -->|Permission Check Passed| ALLOW_ACCESS[Allow Access]
    HIDDEN -->|Permission Check Failed| DENY_ACCESS[Deny Access]
```

## Scalability & Performance Architecture

### 1. Caching Strategy

```mermaid
graph LR
    subgraph "Cache Layers"
        L1[Application Cache]
        L2[Redis Cache] 
        L3[Database]
    end

    subgraph "Cache Keys"
        USER_MENU[user_menu:{user_id}]
        TENANT_MENU[tenant_menu:{tenant_id}]
        SYSTEM_MENU[system_menu]
        USER_PERMS[user_perms:{user_id}]
    end

    REQUEST[Menu Request] --> L1
    L1 -->|Cache Miss| L2
    L2 -->|Cache Miss| L3
    L3 -->|Data| L2
    L2 -->|Cached Data| L1
    L1 -->|Response| CLIENT[Client]

    USER_MENU --> L2
    TENANT_MENU --> L2
    SYSTEM_MENU --> L2
    USER_PERMS --> L2
```

### 2. Database Optimization

**Indexing Strategy**:
```sql
-- Hierarchy traversal
CREATE INDEX idx_menu_hierarchy ON menu_items(parent_id, display_order);

-- Tenant isolation  
CREATE INDEX idx_menu_tenant ON menu_items(tenant_id, is_visible);

-- Permission filtering
CREATE INDEX idx_menu_permission ON menu_items(required_permission);

-- User customizations
CREATE INDEX idx_user_customizations ON user_menu_customizations(user_id);
```

**Query Optimization**:
- Use CTEs for hierarchical queries
- Batch fetch customizations
- Implement query result caching
- Pre-compute common menu structures

## Security Architecture

### 1. Security Boundaries

```mermaid
graph TB
    subgraph "Security Layers"
        AUTH[Authentication Layer]
        AUTHZ[Authorization Layer] 
        TENANT[Tenant Isolation Layer]
        DATA[Data Access Layer]
    end

    subgraph "Security Controls"
        JWT[JWT Tokens]
        RBAC[RBAC Permissions]
        ISOLATION[Tenant Boundaries]
        AUDIT[Audit Logging]
    end

    REQUEST[Client Request] --> AUTH
    AUTH --> JWT
    AUTH --> AUTHZ
    AUTHZ --> RBAC
    AUTHZ --> TENANT
    TENANT --> ISOLATION
    TENANT --> DATA
    DATA --> AUDIT
```

### 2. Attack Vector Mitigation

| Attack Vector | Mitigation Strategy |
|---------------|-------------------|
| **Information Disclosure** | Server-side menu filtering |
| **Privilege Escalation** | Strict permission validation |
| **Tenant Data Leakage** | Tenant isolation in queries |
| **Injection Attacks** | Parameterized queries, input validation |
| **Audit Evasion** | Comprehensive audit logging |

## Extension Points

### 1. Custom Menu Providers

```python
class CustomMenuProvider(ABC):
    """Interface for custom menu providers."""
    
    @abstractmethod
    async def get_menus(self, user: User, context: Dict) -> List[MenuItem]:
        """Provide custom menus for user."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Provider priority for menu ordering."""
        pass
```

### 2. Menu Event Hooks

```python
class MenuEventHandler:
    """Handle menu lifecycle events."""
    
    async def on_menu_created(self, menu_item: MenuItem, user: User):
        """Handle menu creation event."""
        pass
    
    async def on_menu_customized(self, user_id: UUID, customizations: List[Dict]):
        """Handle menu customization event."""
        pass
```

## Deployment Architecture

### 1. Production Deployment

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[NGINX/ALB]
    end

    subgraph "Application Tier"
        APP1[FastAPI Instance 1]
        APP2[FastAPI Instance 2]
        APP3[FastAPI Instance 3]
    end

    subgraph "Cache Tier"
        REDIS1[Redis Primary]
        REDIS2[Redis Replica]
    end

    subgraph "Database Tier"
        DB1[PostgreSQL Primary]
        DB2[PostgreSQL Replica]
    end

    subgraph "Monitoring"
        METRICS[Prometheus]
        LOGS[ELK Stack]
        ALERTS[AlertManager]
    end

    LB --> APP1
    LB --> APP2
    LB --> APP3

    APP1 --> REDIS1
    APP2 --> REDIS1
    APP3 --> REDIS1
    REDIS1 --> REDIS2

    APP1 --> DB1
    APP2 --> DB1
    APP3 --> DB1
    DB1 --> DB2

    APP1 --> METRICS
    APP2 --> METRICS
    APP3 --> METRICS
    METRICS --> ALERTS

    APP1 --> LOGS
    APP2 --> LOGS
    APP3 --> LOGS
```

### 2. Monitoring & Observability

**Key Metrics**:
- Menu request latency
- Cache hit rates
- Permission check performance
- Database query performance
- User customization activity

**Health Checks**:
- Menu service availability
- Database connectivity
- Cache connectivity
- Permission service integration

---

📚 **Next**: [Database Schema](./database-schema.md) - Detailed database design documentation.