// API Configuration
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
export const API_VERSION = 'v1';
export const API_PREFIX = `/api/${API_VERSION}`;

// Authentication
export const TOKEN_STORAGE_KEY = 'sentinel_auth_tokens';
export const USER_STORAGE_KEY = 'sentinel_user';

// App Configuration
export const APP_NAME = 'Sentinel';
export const APP_DESCRIPTION = 'Multi-tenant User Management Platform';

// Role-based access
export const ROLE_PERMISSIONS = {
  super_admin: {
    canManageTenants: true,
    canManageUsers: true,
    canManageRoles: true,
    canViewAllData: true,
  },
  tenant_admin: {
    canManageTenants: false,
    canManageUsers: true,
    canManageRoles: true,
    canViewAllData: false,
  },
  user: {
    canManageTenants: false,
    canManageUsers: false,
    canManageRoles: false,
    canViewAllData: false,
  },
} as const;

// Navigation routes
export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  DASHBOARD: '/dashboard',
  PROFILE: '/profile', 
  USERS: '/users',
  TENANTS: '/tenants',
  ROLES: '/roles',
  SETTINGS: '/settings',
} as const;

// Theme colors (Material Design inspired)
export const THEME_COLORS = {
  primary: 'hsl(221, 83%, 53%)',
  secondary: 'hsl(210, 40%, 98%)',
  accent: 'hsl(142, 76%, 36%)',
  destructive: 'hsl(0, 84%, 60%)',
  muted: 'hsl(210, 40%, 96%)',
  border: 'hsl(214, 32%, 91%)',
  input: 'hsl(214, 32%, 91%)',
  ring: 'hsl(221, 83%, 53%)',
} as const;