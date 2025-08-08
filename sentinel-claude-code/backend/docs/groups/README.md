# Groups API Documentation
> Gotchas
> - Use trailing slash for list endpoints (`/groups/`) to avoid 307 redirects
> - Field name is `metadata` in the API; backend maps to DB column `group_metadata`
> - Parent cycles are rejected with 400; check error message
> - Idempotent operations: adding existing user or assigning existing role returns 0 counts



A practical guide for frontend engineers to integrate with Groups (Module 5).

- Base URL: `http://localhost:8000/api/v1`
- Authentication: JWT Bearer token required
- Tenant isolation: All calls are scoped to the authenticated user's tenant
- Content-Type: `application/json`

## Required scopes

- Read: `group:read`
- Write: `group:write` (update)
- Admin: `group:admin` (create, delete, add/remove users, assign/remove roles)

Include as a space-separated list in JWT token claims; the backend enforces them per-route.

## Endpoint quick reference

- Groups CRUD
  - POST `/groups/` — Create group (scope: group:admin)
  - GET `/groups/` — List groups (scope: group:read)
  - GET `/groups/{group_id}` — Get details (scope: group:read)
  - PATCH `/groups/{group_id}` — Update (scope: group:write)
  - DELETE `/groups/{group_id}` — Soft delete (scope: group:admin)

- Membership management
  - POST `/groups/{group_id}/users` — Add users (scope: group:admin)
  - DELETE `/groups/{group_id}/users/{user_id}` — Remove user (scope: group:admin)
  - GET `/groups/{group_id}/users` — List members (user IDs) (scope: group:read)

- Role assignment
  - POST `/groups/{group_id}/roles` — Assign roles (scope: group:admin)
  - DELETE `/groups/{group_id}/roles/{role_id}` — Remove role (scope: group:admin)
  - GET `/groups/{group_id}/roles` — List roles (role IDs) (scope: group:read)

Note: Prefer trailing slashes for list endpoints (e.g., `/groups/`) to avoid 307 redirects.

## Data model (API shapes)

Group (response):
```
{
  "id": "UUID",
  "tenant_id": "UUID",
  "name": "string",
  "display_name": "string|null",
  "description": "string|null",
  "parent_group_id": "UUID|null",
  "metadata": {"...": "..."},
  "is_active": true,
  "created_at": "ISO timestamp",
  "updated_at": "ISO timestamp"
}
```

Important: In the API, the field is `metadata`. Internally the column is `group_metadata`; the backend handles the aliasing. Always send/consume `metadata` in clients.

List response:
```
{
  "items": [Group, ...],
  "total": number,
  "skip": number,
  "limit": number
}
```

## Filtering, search, sorting, pagination (GET /groups/)

Query params:
- `is_active`: boolean (optional)
- `parent_group_id`: UUID (optional)
- `search`: string (optional; matches `name` and `display_name`, case-insensitive)
- `skip`: number (default 0)
- `limit`: number (default 50, max 100)
- `sort_by`: string (defaults to `name`)
- `sort_order`: `asc`|`desc` (defaults to `asc`)

## Hierarchy rules

- `parent_group_id` must reference an existing group in the same tenant
- Circular dependencies are rejected (e.g., setting A's parent to B and B's parent to A)

## Idempotency

- Adding an already-member user returns `{"added": 0}`
- Assigning an already-assigned role returns `{"assigned": 0}`

## Common error responses

- 400: Validation error (e.g., invalid parent, circular dependency)
- 401: Authentication required/invalid
- 403: Insufficient scope
- 404: Not found (e.g., group in different tenant)
- 409: Conflict (e.g., duplicate group name within tenant)

See `errors.md` for details.

## Examples

See:
- `api-endpoints.md` for endpoint-by-endpoint request/response examples
- `examples.md` for curl and JavaScript usage snippets

