# User Flows & Workflows

> Common user scenarios and workflows for the Menu & Navigation system

## Overview

This document describes the typical user flows and workflows when interacting with the menu system, including both end-user navigation scenarios and administrative menu management tasks.

## Primary User Flows

### 1. User Menu Access Flow

```mermaid
flowchart TD
    START([User Logs In]) --> AUTH{Authentication Successful?}
    AUTH -->|No| LOGIN_ERROR[Show Login Error]
    AUTH -->|Yes| GET_USER_CONTEXT[Get User Context]
    
    GET_USER_CONTEXT --> USER_TENANT[Identify User Tenant]
    USER_TENANT --> USER_ROLES[Get User Roles & Permissions]
    USER_ROLES --> FETCH_MENUS[Fetch Available Menu Items]
    
    FETCH_MENUS --> SYSTEM_MENUS[Get System-wide Menus]
    SYSTEM_MENUS --> TENANT_MENUS[Get Tenant-specific Menus]
    TENANT_MENUS --> FILTER_PERMISSIONS[Filter by User Permissions]
    
    FILTER_PERMISSIONS --> APPLY_CUSTOMIZATIONS[Apply User Customizations]
    APPLY_CUSTOMIZATIONS --> BUILD_HIERARCHY[Build Menu Hierarchy]
    BUILD_HIERARCHY --> RENDER_MENU[Render Menu in UI]
    
    RENDER_MENU --> USER_INTERACTION[User Interacts with Menu]
    USER_INTERACTION --> MENU_CLICK{User Clicks Menu Item?}
    
    MENU_CLICK -->|Yes| VALIDATE_ACCESS[Validate Access Permissions]
    MENU_CLICK -->|No| WAIT_FOR_ACTION[Wait for User Action]
    
    VALIDATE_ACCESS --> ACCESS_GRANTED{Access Granted?}
    ACCESS_GRANTED -->|Yes| NAVIGATE[Navigate to Destination]
    ACCESS_GRANTED -->|No| ACCESS_DENIED[Show Access Denied]
    
    NAVIGATE --> END([User at Destination])
    ACCESS_DENIED --> WAIT_FOR_ACTION
    WAIT_FOR_ACTION --> MENU_CLICK
    
    classDef startEnd fill:#e1f5fe
    classDef process fill:#f3e5f5
    classDef decision fill:#fff3e0
    classDef error fill:#ffebee
    
    class START,END startEnd
    class GET_USER_CONTEXT,USER_TENANT,USER_ROLES,FETCH_MENUS,SYSTEM_MENUS,TENANT_MENUS,FILTER_PERMISSIONS,APPLY_CUSTOMIZATIONS,BUILD_HIERARCHY,RENDER_MENU,VALIDATE_ACCESS,NAVIGATE process
    class AUTH,MENU_CLICK,ACCESS_GRANTED decision
    class LOGIN_ERROR,ACCESS_DENIED error
```

### 2. Menu Customization Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant MenuService
    participant Database

    User->>Frontend: Open Menu Settings
    Frontend->>API: GET /navigation/menu
    API->>MenuService: get_user_menu(user_id)
    MenuService->>Database: Get menu items + customizations
    Database-->>MenuService: Current menu structure
    MenuService-->>API: UserMenuResponse
    API-->>Frontend: Menu with current customizations
    Frontend-->>User: Show customizable menu

    User->>Frontend: Hide/Show menu items
    User->>Frontend: Reorder menu items
    User->>Frontend: Save customizations
    
    Frontend->>API: POST /navigation/customize
    API->>MenuService: customize_user_menu(user_id, changes)
    MenuService->>Database: Update user_menu_customizations
    Database-->>MenuService: Confirmation
    MenuService-->>API: Success response
    API-->>Frontend: Customizations saved
    Frontend-->>User: Updated menu displayed
```

### 3. Permission-Based Menu Filtering

```mermaid
flowchart TD
    START[Menu Request for User] --> GET_MENUS[Get All Potential Menu Items]
    GET_MENUS --> LOOP_START[For Each Menu Item]
    
    LOOP_START --> CHECK_VISIBLE{Menu Item Visible?}
    CHECK_VISIBLE -->|No| NEXT_ITEM[Next Menu Item]
    CHECK_VISIBLE -->|Yes| CHECK_PERM_REQ{Permission Required?}
    
    CHECK_PERM_REQ -->|No| INCLUDE_MENU[Include in User Menu]
    CHECK_PERM_REQ -->|Yes| CHECK_USER_PERM{User Has Permission?}
    
    CHECK_USER_PERM -->|No| CHECK_RESOURCE{Menu Links to Resource?}
    CHECK_USER_PERM -->|Yes| INCLUDE_MENU
    
    CHECK_RESOURCE -->|No| EXCLUDE_MENU[Exclude from Menu]
    CHECK_RESOURCE -->|Yes| CHECK_RESOURCE_PERM{Has Resource Permission?}
    
    CHECK_RESOURCE_PERM -->|Yes| INCLUDE_MENU
    CHECK_RESOURCE_PERM -->|No| EXCLUDE_MENU
    
    INCLUDE_MENU --> NEXT_ITEM
    EXCLUDE_MENU --> NEXT_ITEM
    NEXT_ITEM --> MORE_ITEMS{More Menu Items?}
    
    MORE_ITEMS -->|Yes| LOOP_START
    MORE_ITEMS -->|No| BUILD_HIERARCHY[Build Menu Hierarchy]
    BUILD_HIERARCHY --> FINAL_MENU[Return Filtered Menu]
    
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef result fill:#e3f2fd
    
    class START,GET_MENUS,LOOP_START,INCLUDE_MENU,EXCLUDE_MENU,NEXT_ITEM,BUILD_HIERARCHY process
    class CHECK_VISIBLE,CHECK_PERM_REQ,CHECK_USER_PERM,CHECK_RESOURCE,CHECK_RESOURCE_PERM,MORE_ITEMS decision
    class FINAL_MENU result
```

## Administrative Flows

### 1. Menu Item Creation Flow (Admin)

```mermaid
sequenceDiagram
    participant Admin
    participant Frontend
    participant API
    participant MenuService
    participant PermissionService
    participant Database

    Admin->>Frontend: Access Menu Administration
    Frontend->>API: GET /navigation/menu-items (with admin token)
    API->>PermissionService: Verify admin permissions
    PermissionService-->>API: Permission granted
    API->>MenuService: list_menu_items()
    MenuService->>Database: Get all menu items
    Database-->>MenuService: Menu items list
    MenuService-->>API: MenuItemListResponse
    API-->>Frontend: Current menu structure
    Frontend-->>Admin: Show menu management interface

    Admin->>Frontend: Create new menu item
    Frontend->>Admin: Show creation form
    Admin->>Frontend: Fill menu item details
    Admin->>Frontend: Submit new menu item

    Frontend->>API: POST /navigation/menu-items
    API->>PermissionService: Verify admin permissions
    PermissionService-->>API: Permission granted
    API->>MenuService: create_menu_item(data)
    MenuService->>MenuService: Validate menu data
    MenuService->>Database: Check for duplicates
    Database-->>MenuService: No duplicates found
    MenuService->>Database: Insert menu item
    Database-->>MenuService: Created menu item
    MenuService-->>API: MenuItemResponse
    API-->>Frontend: Menu item created
    Frontend-->>Admin: Success confirmation
```

### 2. Hierarchical Menu Organization

```mermaid
graph TD
    subgraph "Menu Hierarchy Creation"
        ADMIN[Admin Creates Menu Structure]
        
        subgraph "Level 1 - Main Categories"
            MAIN1[Dashboard]
            MAIN2[Operations] 
            MAIN3[Administration]
            MAIN4[Reports]
        end
        
        subgraph "Level 2 - Sub Categories"
            SUB1[User Management]
            SUB2[Tenant Management]
            SUB3[Role Management]
            
            SUB4[Inventory]
            SUB5[Orders]
            SUB6[Shipping]
        end
        
        subgraph "Level 3 - Specific Functions"
            FUNC1[Create User]
            FUNC2[Edit User]
            FUNC3[Delete User]
            
            FUNC4[View Inventory]
            FUNC5[Add Stock]
            FUNC6[Inventory Reports]
        end
    end

    ADMIN --> MAIN1
    ADMIN --> MAIN2
    ADMIN --> MAIN3
    ADMIN --> MAIN4

    MAIN3 --> SUB1
    MAIN3 --> SUB2
    MAIN3 --> SUB3

    MAIN2 --> SUB4
    MAIN2 --> SUB5
    MAIN2 --> SUB6

    SUB1 --> FUNC1
    SUB1 --> FUNC2
    SUB1 --> FUNC3

    SUB4 --> FUNC4
    SUB4 --> FUNC5
    SUB4 --> FUNC6

    classDef admin fill:#ffcdd2
    classDef level1 fill:#c8e6c9
    classDef level2 fill:#bbdefb
    classDef level3 fill:#fff9c4
    
    class ADMIN admin
    class MAIN1,MAIN2,MAIN3,MAIN4 level1
    class SUB1,SUB2,SUB3,SUB4,SUB5,SUB6 level2
    class FUNC1,FUNC2,FUNC3,FUNC4,FUNC5,FUNC6 level3
```

## Industry-Specific Workflows

### 1. Maritime Operations Menu Flow

```mermaid
flowchart LR
    subgraph "Maritime User Login"
        MAR_USER[Maritime Operations User]
        MAR_LOGIN[Login to System]
    end

    subgraph "System-wide Menus"
        DASHBOARD[Dashboard]
        PROFILE[User Profile]
    end

    subgraph "Maritime-specific Menus"
        PORT_OPS[Port Operations]
        VESSEL_MGT[Vessel Management]
        CARGO_MAN[Cargo Manifest]
        CUSTOMS[Customs Clearance]
        SECURITY[Port Security]
    end

    subgraph "Permission Filters"
        BASIC_PERM[Basic Operations]
        CUSTOMS_PERM[Customs Permissions]
        SECURITY_PERM[Security Clearance]
    end

    subgraph "Final Menu Structure"
        FINAL_MENU[Personalized Maritime Menu]
    end

    MAR_USER --> MAR_LOGIN
    MAR_LOGIN --> DASHBOARD
    MAR_LOGIN --> PROFILE
    MAR_LOGIN --> PORT_OPS
    MAR_LOGIN --> VESSEL_MGT
    MAR_LOGIN --> CARGO_MAN

    CUSTOMS --> CUSTOMS_PERM
    SECURITY --> SECURITY_PERM
    
    CUSTOMS_PERM -->|Has Permission| FINAL_MENU
    SECURITY_PERM -->|Has Permission| FINAL_MENU
    
    DASHBOARD --> FINAL_MENU
    PROFILE --> FINAL_MENU
    PORT_OPS --> BASIC_PERM
    VESSEL_MGT --> BASIC_PERM
    CARGO_MAN --> BASIC_PERM
    BASIC_PERM --> FINAL_MENU
```

### 2. Air Cargo Operations Menu Flow

```mermaid
flowchart TD
    AIR_USER[Air Cargo User] --> CHECK_ROLE{User Role?}
    
    CHECK_ROLE -->|Operations Manager| FULL_ACCESS[Full Air Cargo Menu]
    CHECK_ROLE -->|Ground Handler| LIMITED_ACCESS[Limited Ground Menu]
    CHECK_ROLE -->|Security Officer| SECURITY_ACCESS[Security-focused Menu]

    FULL_ACCESS --> FLIGHT_COORD[Flight Coordination]
    FULL_ACCESS --> CARGO_HANDLE[Cargo Handling]
    FULL_ACCESS --> FREIGHT_MGT[Freight Management]
    FULL_ACCESS --> GROUND_SERVICES[Ground Services]
    FULL_ACCESS --> AIR_SECURITY[Security Screening]

    LIMITED_ACCESS --> CARGO_HANDLE
    LIMITED_ACCESS --> GROUND_SERVICES

    SECURITY_ACCESS --> AIR_SECURITY
    SECURITY_ACCESS --> INCIDENT_REPORT[Incident Reporting]

    classDef user fill:#e1f5fe
    classDef decision fill:#fff3e0
    classDef access fill:#e8f5e8
    classDef menu fill:#f3e5f5

    class AIR_USER user
    class CHECK_ROLE decision
    class FULL_ACCESS,LIMITED_ACCESS,SECURITY_ACCESS access
    class FLIGHT_COORD,CARGO_HANDLE,FREIGHT_MGT,GROUND_SERVICES,AIR_SECURITY,INCIDENT_REPORT menu
```

## Error Handling Flows

### 1. Permission Denied Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant MenuService
    participant PermissionService
    participant AuditLog

    User->>Frontend: Click restricted menu item
    Frontend->>API: Request menu item access
    API->>PermissionService: Check user permissions
    PermissionService-->>API: Permission denied
    API->>AuditLog: Log access attempt
    API-->>Frontend: 403 Forbidden
    Frontend-->>User: Show access denied message
    User->>Frontend: Request access or contact admin
    Frontend->>Frontend: Show contact information
```

### 2. Menu Loading Error Flow

```mermaid
flowchart TD
    START[User Requests Menu] --> FETCH_MENU[Fetch Menu from API]
    FETCH_MENU --> API_ERROR{API Error?}
    
    API_ERROR -->|No Error| SUCCESS[Display Menu]
    API_ERROR -->|Timeout| RETRY{Retry Attempts < 3?}
    API_ERROR -->|Server Error| LOG_ERROR[Log Error]
    API_ERROR -->|Network Error| CHECK_CONNECTION[Check Connection]
    
    RETRY -->|Yes| WAIT[Wait 1 Second]
    RETRY -->|No| FALLBACK[Show Cached Menu]
    
    WAIT --> FETCH_MENU
    
    LOG_ERROR --> FALLBACK
    CHECK_CONNECTION --> FALLBACK
    
    FALLBACK --> CACHE_AVAILABLE{Cached Menu Available?}
    CACHE_AVAILABLE -->|Yes| SHOW_CACHED[Display Cached Menu + Warning]
    CACHE_AVAILABLE -->|No| SHOW_ERROR[Show Error Page]
    
    classDef normal fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef error fill:#ffebee
    classDef success fill:#e3f2fd
    
    class START,FETCH_MENU,WAIT,LOG_ERROR,CHECK_CONNECTION,FALLBACK normal
    class API_ERROR,RETRY,CACHE_AVAILABLE decision
    class SHOW_ERROR error
    class SUCCESS,SHOW_CACHED success
```

## Performance Optimization Flows

### 1. Menu Caching Strategy

```mermaid
flowchart TD
    REQUEST[Menu Request] --> CHECK_CACHE{Menu in Cache?}
    
    CHECK_CACHE -->|Hit| VALIDATE_CACHE{Cache Valid?}
    CHECK_CACHE -->|Miss| FETCH_DB[Fetch from Database]
    
    VALIDATE_CACHE -->|Valid| RETURN_CACHED[Return Cached Menu]
    VALIDATE_CACHE -->|Expired| REFRESH[Refresh Cache]
    
    FETCH_DB --> BUILD_MENU[Build Menu Structure]
    REFRESH --> BUILD_MENU
    
    BUILD_MENU --> APPLY_PERMISSIONS[Apply Permission Filters]
    APPLY_PERMISSIONS --> APPLY_CUSTOMIZATIONS[Apply User Customizations]
    APPLY_CUSTOMIZATIONS --> CACHE_RESULT[Cache Result]
    CACHE_RESULT --> RETURN_MENU[Return Menu to User]
    
    RETURN_CACHED --> END[Menu Displayed]
    RETURN_MENU --> END
    
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef cache fill:#e3f2fd
    classDef result fill:#c8e6c9
    
    class REQUEST,FETCH_DB,BUILD_MENU,APPLY_PERMISSIONS,APPLY_CUSTOMIZATIONS,REFRESH process
    class CHECK_CACHE,VALIDATE_CACHE decision
    class RETURN_CACHED,CACHE_RESULT cache
    class RETURN_MENU,END result
```

### 2. Batch Menu Operations

```mermaid
sequenceDiagram
    participant Admin
    participant Frontend
    participant API
    participant MenuService
    participant Database

    Admin->>Frontend: Select multiple menu items
    Admin->>Frontend: Choose bulk action (hide/show/reorder)
    Frontend->>API: POST /navigation/bulk-customize
    
    API->>MenuService: process_bulk_customizations(user_id, batch)
    MenuService->>MenuService: Validate all changes
    MenuService->>Database: Begin transaction
    MenuService->>Database: Batch update customizations
    Database-->>MenuService: All updates successful
    MenuService->>Database: Commit transaction
    MenuService-->>API: Bulk operation complete
    API-->>Frontend: Success with updated menu
    Frontend-->>Admin: Show updated menu structure
```

## Integration Workflows

### 1. Real-time Menu Updates

```mermaid
sequenceDiagram
    participant Admin
    participant MenuAPI
    participant MenuService
    participant WebSocket
    participant UserClient

    Admin->>MenuAPI: Update menu item
    MenuAPI->>MenuService: Update menu in database
    MenuService-->>MenuAPI: Menu updated
    MenuService->>WebSocket: Broadcast menu change
    WebSocket->>UserClient: Menu update notification
    UserClient->>MenuAPI: Request updated menu
    MenuAPI-->>UserClient: Send updated menu
    UserClient->>UserClient: Update UI with new menu
```

### 2. Permission Change Impact

```mermaid
flowchart TD
    PERM_CHANGE[User Permission Changed] --> INVALIDATE_CACHE[Invalidate Menu Cache]
    INVALIDATE_CACHE --> NOTIFY_USER[Notify User of Changes]
    NOTIFY_USER --> USER_REFRESH{User Refreshes?}
    
    USER_REFRESH -->|Yes| REBUILD_MENU[Rebuild Menu with New Permissions]
    USER_REFRESH -->|No| NEXT_REQUEST[Wait for Next Menu Request]
    
    REBUILD_MENU --> NEW_MENU[Display Updated Menu]
    NEXT_REQUEST --> REBUILD_MENU
    
    classDef trigger fill:#ffcdd2
    classDef process fill:#e8f5e8
    classDef decision fill:#fff3e0
    classDef result fill:#c8e6c9
    
    class PERM_CHANGE trigger
    class INVALIDATE_CACHE,NOTIFY_USER,REBUILD_MENU,NEXT_REQUEST process
    class USER_REFRESH decision
    class NEW_MENU result
```

---

📚 **Next**: [Implementation Guide](./implementation.md) - Technical implementation details for developers.