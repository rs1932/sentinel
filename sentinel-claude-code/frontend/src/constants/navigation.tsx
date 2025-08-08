import {
  Users,
  Building2,
  Shield,
  Settings,
  LayoutDashboard,
  UserCog,
  Home,
  UsersRound,
  Lock,
} from 'lucide-react';
import { MenuItem } from '@/types';
import { ROUTES } from '@/constants';

export const NAVIGATION_MENUS: Record<string, MenuItem[]> = {
  super_admin: [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      path: ROUTES.DASHBOARD,
      roles: ['super_admin'],
    },
    {
      id: 'tenants',
      label: 'Tenants',
      icon: Building2,
      path: ROUTES.TENANTS,
      roles: ['super_admin'],
    },
    {
      id: 'users',
      label: 'Users',
      icon: Users,
      path: ROUTES.USERS,
      roles: ['super_admin'],
    },
    {
      id: 'groups',
      label: 'Groups',
      icon: UsersRound,
      path: ROUTES.GROUPS,
      roles: ['super_admin'],
    },
    {
      id: 'roles',
      label: 'Roles',
      icon: Shield,
      path: ROUTES.ROLES,
      roles: ['super_admin'],
    },
    {
      id: 'permissions',
      label: 'Permissions',
      icon: Lock,
      path: ROUTES.PERMISSIONS,
      roles: ['super_admin'],
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: Settings,
      path: ROUTES.SETTINGS,
      roles: ['super_admin'],
    },
  ],
  tenant_admin: [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      path: ROUTES.DASHBOARD,
      roles: ['tenant_admin'],
    },
    {
      id: 'users',
      label: 'Users',
      icon: Users,
      path: ROUTES.USERS,
      roles: ['tenant_admin'],
    },
    {
      id: 'groups',
      label: 'Groups',
      icon: UsersRound,
      path: ROUTES.GROUPS,
      roles: ['tenant_admin'],
    },
    {
      id: 'roles',
      label: 'Roles',
      icon: Shield,
      path: ROUTES.ROLES,
      roles: ['tenant_admin'],
    },
    {
      id: 'permissions',
      label: 'Permissions',
      icon: Lock,
      path: ROUTES.PERMISSIONS,
      roles: ['tenant_admin'],
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: UserCog,
      path: ROUTES.PROFILE,
      roles: ['tenant_admin'],
    },
  ],
  user: [
    {
      id: 'home',
      label: 'Home',
      icon: Home,
      path: ROUTES.HOME,
      roles: ['user'],
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: UserCog,
      path: ROUTES.PROFILE,
      roles: ['user'],
    },
  ],
};