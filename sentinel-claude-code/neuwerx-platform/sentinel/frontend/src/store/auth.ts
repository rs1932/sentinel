import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthTokens, UserRole } from '@/types';
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '@/constants';
import { hasAdminAccess } from '@/lib/auth/adminCheck';
import { getScopesFromToken, isTokenExpired as isJWTExpired } from '@/lib/jwt';

// Session timeout: 30 minutes of inactivity
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  userRole: UserRole | null;
  tokenExpiresAt: number | null; // Unix timestamp
  hasAdminAccess: boolean; // Whether user has admin access to Sentinel
  lastActivity: number | null; // Last activity timestamp for session timeout
}

interface AuthActions {
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  setLoading: (loading: boolean) => void;
  getUserRole: () => UserRole | null;
  refreshToken: () => Promise<boolean>;
  isTokenExpired: () => boolean;
  getTimeUntilExpiry: () => number;
  checkAdminAccess: () => boolean;
  getUserScopes: () => string[];
  updateActivity: () => void;
  isSessionExpired: () => boolean;
}

// Helper function to determine user role
const determineUserRole = (user: User): UserRole => {
  // First check if user has role info in attributes (for superadmin)
  if (user.attributes?.role) {
    if (user.attributes.role === 'superadmin') {
      return 'super_admin';
    }
    if (user.attributes.role.includes('admin')) {
      return 'tenant_admin';
    }
  }

  // Check if user is on PLATFORM tenant (superadmin tenant)
  if (user.tenant?.code === 'PLATFORM' || user.tenant_id === '00000000-0000-0000-0000-000000000000') {
    return 'super_admin';
  }

  // Check if user has formal role assignments
  if (user.roles && user.roles.length > 0) {
    // Check for system admin roles
    const hasSystemAdminRole = user.roles.some(
      (role) => role.type === 'system' && (role.name === 'admin' || role.name === 'superadmin')
    );
    
    if (hasSystemAdminRole) {
      return 'super_admin';
    }
    
    // Check for tenant admin roles
    const hasTenantAdminRole = user.roles.some(
      (role) => role.name.toLowerCase().includes('admin') || role.name === 'tenant_admin' || role.name.toLowerCase().includes('manager')
    );
    
    if (hasTenantAdminRole) {
      return 'tenant_admin';
    }
  }
  
  return 'user';
};

export const useAuthStore = create<AuthState & AuthActions>()(
  persist(
    (set, get) => ({
      // State
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      userRole: null,
      tokenExpiresAt: null,
      hasAdminAccess: false,
      lastActivity: null,

      // Actions
      login: (user: User, tokens: AuthTokens) => {
        const userRole = determineUserRole(user);
        const expiresAt = Date.now() + (tokens.expires_in * 1000);
        const scopes = getScopesFromToken(tokens.access_token);
        const adminAccess = hasAdminAccess(scopes);
        
        set({
          user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
          userRole,
          tokenExpiresAt: expiresAt,
          hasAdminAccess: adminAccess,
          lastActivity: Date.now(),
        });
      },

      logout: () => {
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
          userRole: null,
          tokenExpiresAt: null,
          hasAdminAccess: false,
          lastActivity: null,
        });
        // Clear sessionStorage and localStorage (for any legacy data)
        sessionStorage.removeItem('auth-storage');
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      },

      setUser: (user: User) => {
        const userRole = determineUserRole(user);
        const { tokens } = get();
        const scopes = tokens ? getScopesFromToken(tokens.access_token) : [];
        const adminAccess = hasAdminAccess(scopes);
        set({ user, userRole, hasAdminAccess: adminAccess });
      },

      setTokens: (tokens: AuthTokens) => {
        const expiresAt = Date.now() + (tokens.expires_in * 1000);
        set({ tokens, tokenExpiresAt: expiresAt });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      getUserRole: () => {
        const { user } = get();
        return user ? determineUserRole(user) : null;
      },

      refreshToken: async () => {
        const { tokens } = get();
        if (!tokens?.refresh_token) {
          return false;
        }

        try {
          set({ isLoading: true });
          
          // Import apiClient dynamically to avoid circular dependency
          const { apiClient } = await import('@/lib/api/client');
          
          const response = await apiClient.auth.refresh(tokens.refresh_token);
          const { access_token, refresh_token, token_type, expires_in } = response;

          const newTokens = {
            access_token,
            refresh_token,
            token_type,
            expires_in,
          };

          // Update tokens and expiration
          const expiresAt = Date.now() + (expires_in * 1000);
          set({ 
            tokens: newTokens, 
            tokenExpiresAt: expiresAt,
            isLoading: false 
          });

          // Update API client with new token
          apiClient.setToken(access_token);

          return true;
        } catch (error) {
          console.error('Token refresh failed:', error);
          // If refresh fails, logout user
          get().logout();
          return false;
        }
      },

      isTokenExpired: () => {
        const { tokens, tokenExpiresAt } = get();
        
        // First check if we have tokens
        if (!tokens?.access_token) return true;
        
        // Use JWT expiration check for more accuracy
        const jwtExpired = isJWTExpired(tokens.access_token);
        
        // Also check stored expiration as fallback
        const storedExpired = tokenExpiresAt ? Date.now() >= (tokenExpiresAt - 300000) : true;
        
        return jwtExpired || storedExpired;
      },

      getTimeUntilExpiry: () => {
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) return 0;
        
        const timeLeft = tokenExpiresAt - Date.now();
        return Math.max(0, Math.floor(timeLeft / 1000)); // Return seconds
      },

      checkAdminAccess: () => {
        const { tokens } = get();
        if (!tokens?.access_token) return false;
        const scopes = getScopesFromToken(tokens.access_token);
        return hasAdminAccess(scopes);
      },

      getUserScopes: () => {
        const { tokens } = get();
        if (!tokens?.access_token) return [];
        return getScopesFromToken(tokens.access_token);
      },

      updateActivity: () => {
        set({ lastActivity: Date.now() });
      },

      isSessionExpired: () => {
        const { lastActivity } = get();
        if (!lastActivity) return false; // No activity recorded yet
        
        return Date.now() - lastActivity > SESSION_TIMEOUT_MS;
      },
    }),
  {
    name: 'auth-storage',
    storage: createJSONStorage(() => localStorage), // Keep localStorage but add session timeout
    partialize: (state) => ({
      user: state.user,
      tokens: state.tokens,
      isAuthenticated: state.isAuthenticated,
      userRole: state.userRole,
      tokenExpiresAt: state.tokenExpiresAt,
      hasAdminAccess: state.hasAdminAccess,
      lastActivity: state.lastActivity,
    }),
    onRehydrateStorage: () => (state) => {
      // Check if token or session is expired after rehydration
      if (state && state.isAuthenticated && state.tokens?.access_token) {
        // Check JWT expiration
        if (isJWTExpired(state.tokens.access_token)) {
          console.warn('Token expired on rehydration, logging out user');
          state.logout();
          return;
        }
        
        // Check session expiration (30 minutes of inactivity)
        if (state.isSessionExpired()) {
          console.warn('Session expired due to inactivity, logging out user');
          state.logout();
          return;
        }
        
        // Update activity on rehydration to prevent immediate timeout
        state.updateActivity();
      }
    },
  })
);