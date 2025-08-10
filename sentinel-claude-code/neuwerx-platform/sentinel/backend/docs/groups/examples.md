# Groups API — Usage Examples

All examples assume you already have an access token (JWT) with the appropriate scopes.

## curl

Create group
```
curl -X POST http://localhost:8000/api/v1/groups/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "apac-ops",
    "display_name": "APAC Ops",
    "description": "Operations in APAC",
    "metadata": {"region": "APAC"},
    "is_active": true
  }'
```

List groups
```
curl -s http://localhost:8000/api/v1/groups/?search=apac \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Add users to a group
```
curl -X POST http://localhost:8000/api/v1/groups/$GROUP_ID/users \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_ids": ["<USER_ID>"]}'
```

Assign roles to a group
```
curl -X POST http://localhost:8000/api/v1/groups/$GROUP_ID/roles \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_ids": ["<ROLE_ID>"]}'
```

## JavaScript (fetch)

Create group
```
const res = await fetch("/api/v1/groups/", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    name: "apac-ops",
    display_name: "APAC Ops",
    description: "Operations in APAC",
    metadata: { region: "APAC" },
    is_active: true,
  }),
});
const group = await res.json();
```

List groups with search and pagination
```
const params = new URLSearchParams({ search: "apac", skip: "0", limit: "25" });
const res = await fetch(`/api/v1/groups/?${params}`, { headers: { Authorization: `Bearer ${token}` } });
const data = await res.json();
```

Add/remove user
```
await fetch(`/api/v1/groups/${groupId}/users`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  body: JSON.stringify({ user_ids: [userId] }),
});

await fetch(`/api/v1/groups/${groupId}/users/${userId}`, {
  method: "DELETE",
  headers: { Authorization: `Bearer ${token}` },
});
```

Assign/remove role
```
await fetch(`/api/v1/groups/${groupId}/roles`, {
  method: "POST",
  headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
  body: JSON.stringify({ role_ids: [roleId] }),
});

await fetch(`/api/v1/groups/${groupId}/roles/${roleId}`, {
  method: "DELETE",
  headers: { Authorization: `Bearer ${token}` },
});
```

## React Query (example)
```
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function useGroups(token) {
  return useQuery({
    queryKey: ["groups"],
    queryFn: async () => {
      const res = await fetch(`/api/v1/groups/`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error("Failed to load groups");
      return res.json();
    },
  });
}

export function useCreateGroup(token) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload) => {
      const res = await fetch(`/api/v1/groups/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Create group failed");
      return res.json();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["groups"] }),
  });
}
```

