# Database Schema Documentation

> Detailed database schema for the Menu & Navigation system

## Overview

The menu system uses two primary tables with foreign key relationships to the core RBAC system. The design supports hierarchical menu structures, tenant isolation, and user customization.

## Primary Tables

### 1. `sentinel.menu_items`

**Purpose**: Stores the hierarchical menu structure with tenant isolation and RBAC integration.

#### Column Details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PRIMARY KEY, NOT NULL, DEFAULT `uuid_generate_v4()` | Unique identifier for the menu item |
| `tenant_id` | `UUID` | FOREIGN KEY → `tenants.id`, NULL | Tenant ownership (NULL = system-wide) |
| `parent_id` | `UUID` | FOREIGN KEY → `menu_items.id`, NULL | Parent menu item (NULL = top-level) |
| `name` | `VARCHAR(100)` | NOT NULL, UNIQUE per parent+tenant | Internal identifier/slug |
| `display_name` | `VARCHAR(255)` | NULL | User-friendly display name |
| `icon` | `VARCHAR(50)` | NULL | Icon identifier/class name |
| `url` | `VARCHAR(500)` | NULL | Navigation URL/route |
| `resource_id` | `UUID` | FOREIGN KEY → `resources.id`, NULL | Linked system resource |
| `required_permission` | `VARCHAR(255)` | NULL | Required permission to view |
| `display_order` | `INTEGER` | DEFAULT 0 | Sort order within parent |
| `is_visible` | `BOOLEAN` | DEFAULT TRUE | Global visibility flag |
| `menu_metadata` | `JSONB` | DEFAULT '{}' | Additional configuration data |
| `created_at` | `TIMESTAMPTZ` | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

#### Foreign Key Relationships

```sql
-- Tenant relationship (nullable for system-wide items)
FOREIGN KEY (tenant_id) REFERENCES sentinel.tenants(id) ON DELETE CASCADE

-- Self-referencing for hierarchy
FOREIGN KEY (parent_id) REFERENCES sentinel.menu_items(id) ON DELETE CASCADE

-- Resource linking
FOREIGN KEY (resource_id) REFERENCES sentinel.resources(id) ON DELETE SET NULL
```

#### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_menu_items_tenant_id ON sentinel.menu_items(tenant_id);
CREATE INDEX idx_menu_items_parent_id ON sentinel.menu_items(parent_id);
CREATE INDEX idx_menu_items_display_order ON sentinel.menu_items(display_order);

-- Unique constraint for name within parent+tenant scope
CREATE UNIQUE INDEX idx_menu_items_unique_name 
ON sentinel.menu_items(name, parent_id, tenant_id);
```

### 2. `sentinel.user_menu_customizations`

**Purpose**: Stores user-specific menu customizations (hide/show, reordering).

#### Column Details

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `UUID` | PRIMARY KEY, NOT NULL, DEFAULT `uuid_generate_v4()` | Unique identifier |
| `user_id` | `UUID` | FOREIGN KEY → `users.id`, NOT NULL | User who made customization |
| `menu_item_id` | `UUID` | FOREIGN KEY → `menu_items.id`, NOT NULL | Menu item being customized |
| `is_hidden` | `BOOLEAN` | DEFAULT FALSE | Whether user has hidden this item |
| `custom_order` | `INTEGER` | NULL | User's preferred order (overrides display_order) |
| `created_at` | `TIMESTAMPTZ` | DEFAULT CURRENT_TIMESTAMP | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT CURRENT_TIMESTAMP | Last update timestamp |

#### Foreign Key Relationships

```sql
-- User relationship
FOREIGN KEY (user_id) REFERENCES sentinel.users(id) ON DELETE CASCADE

-- Menu item relationship  
FOREIGN KEY (menu_item_id) REFERENCES sentinel.menu_items(id) ON DELETE CASCADE
```

#### Unique Constraints

```sql
-- One customization per user per menu item
UNIQUE(user_id, menu_item_id)
```

## Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│    tenants      │←────────┤   menu_items     │
│                 │         │                  │
│ • id (PK)       │         │ • id (PK)        │
│ • name          │         │ • tenant_id (FK) │
│ • code          │         │ • parent_id (FK) │
└─────────────────┘         │ • name           │
                            │ • display_name   │
┌─────────────────┐         │ • icon           │
│    resources    │←────────┤ • url            │
│                 │         │ • resource_id(FK)│
│ • id (PK)       │         │ • required_perm  │
│ • name          │         │ • display_order  │
│ • code          │         │ • is_visible     │
└─────────────────┘         │ • menu_metadata  │
                            └──────────────────┘
                                     ↑│
                      ┌──────────────┘│
                      │               │
                      │               ↓
                      │    ┌──────────────────┐
                      │    │user_menu_custom- │
┌─────────────────┐   │    │izations          │
│     users       │───┼────┤                  │
│                 │   │    │ • id (PK)        │
│ • id (PK)       │   │    │ • user_id (FK)   │
│ • email         │   │    │ • menu_item_id   │
│ • tenant_id     │   │    │ • is_hidden      │
└─────────────────┘   │    │ • custom_order   │
                      │    └──────────────────┘
                      │
                      └─── Self-referencing
                           parent_id → id
```

## Data Flow Examples

### 1. System-wide Menu Structure

```
Dashboard (tenant_id: NULL)
└── Administration (tenant_id: NULL, required_permission: 'admin:read')
    ├── User Management (required_permission: 'users:manage')
    ├── Tenant Management (required_permission: 'tenants:manage')
    └── Role Management (required_permission: 'roles:manage')
```

### 2. Tenant-specific Menu Structure

```sql
-- Maritime tenant menu structure
INSERT INTO menu_items (tenant_id, name, display_name, display_order) 
VALUES ('maritime-tenant-id', 'port-operations', 'Port Operations', 10);

INSERT INTO menu_items (tenant_id, parent_id, name, display_name, display_order)
VALUES ('maritime-tenant-id', 'port-ops-id', 'vessel-management', 'Vessel Management', 10);
```

### 3. User Customization Example

```sql
-- User hides a menu item and reorders another
INSERT INTO user_menu_customizations (user_id, menu_item_id, is_hidden, custom_order)
VALUES 
  ('user-id', 'vessel-mgmt-id', TRUE, NULL),  -- Hide vessel management
  ('user-id', 'berth-assign-id', FALSE, 5);  -- Reorder berth assignment
```

## Query Patterns

### Hierarchical Menu Building

```sql
-- Recursive CTE to build menu hierarchy
WITH RECURSIVE menu_hierarchy AS (
  -- Base case: top-level items
  SELECT id, name, display_name, parent_id, 0 as level, 
         ARRAY[display_order] as path
  FROM menu_items 
  WHERE parent_id IS NULL
  
  UNION ALL
  
  -- Recursive case: children
  SELECT m.id, m.name, m.display_name, m.parent_id, h.level + 1,
         h.path || m.display_order
  FROM menu_items m
  JOIN menu_hierarchy h ON m.parent_id = h.id
)
SELECT * FROM menu_hierarchy ORDER BY path;
```

### User Menu with Customizations

```sql
-- Get user's customized menu
SELECT 
  mi.*,
  COALESCE(umc.is_hidden, FALSE) as user_hidden,
  COALESCE(umc.custom_order, mi.display_order) as effective_order
FROM menu_items mi
LEFT JOIN user_menu_customizations umc 
  ON mi.id = umc.menu_item_id AND umc.user_id = $1
WHERE (mi.tenant_id IS NULL OR mi.tenant_id = $2)
  AND mi.is_visible = TRUE
  AND COALESCE(umc.is_hidden, FALSE) = FALSE
ORDER BY effective_order;
```

## Performance Considerations

### Indexes for Common Queries

```sql
-- Hierarchical queries
CREATE INDEX idx_menu_hierarchy ON menu_items(parent_id, display_order);

-- User customization lookups  
CREATE INDEX idx_user_customizations ON user_menu_customizations(user_id, menu_item_id);

-- Tenant-specific queries
CREATE INDEX idx_menu_tenant_visible ON menu_items(tenant_id, is_visible, display_order);

-- Permission-based filtering
CREATE INDEX idx_menu_permissions ON menu_items(required_permission) 
WHERE required_permission IS NOT NULL;
```

### Query Optimization Tips

1. **Use specific tenant filters** to limit result sets
2. **Index on composite keys** for multi-column WHERE clauses  
3. **Avoid N+1 queries** by fetching customizations in batch
4. **Consider materialized views** for complex permission calculations

## Schema Migration Notes

### Adding New Columns

```sql
-- Example: Adding a new metadata field
ALTER TABLE menu_items 
ADD COLUMN workflow_enabled BOOLEAN DEFAULT FALSE;

-- Update existing records if needed
UPDATE menu_items SET workflow_enabled = TRUE 
WHERE menu_metadata->>'category' = 'workflow';
```

### Data Integrity

- **Cascade deletions** handle cleanup automatically
- **Foreign key constraints** prevent orphaned records
- **Unique constraints** enforce business rules
- **Check constraints** can be added for data validation

---

📚 **Next**: [RBAC Integration](./rbac-integration.md) - Learn how menus integrate with the permission system.