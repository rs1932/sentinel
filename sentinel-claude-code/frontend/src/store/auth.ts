import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, AuthTokens, UserRole } from '@/types';
import { TOKEN_STORAGE_KEY, USER_STORAGE_KEY } from '@/constants';

interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  userRole: UserRole | null;
  tokenExpiresAt: number | null; // Unix timestamp
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
}

// Helper function to determine user role
const determineUserRole = (user: User): UserRole => {
  // Check if user has super admin role
  const hasSystemAdminRole = user.roles.some(
    (role) => role.type === 'system' && role.name === 'admin'
  );
  
  if (hasSystemAdminRole) {
    return 'super_admin';
  }
  
  // Check if user has tenant admin role
  const hasTenantAdminRole = user.roles.some(
    (role) => role.name.includes('admin') || role.name === 'tenant_admin'
  );
  
  if (hasTenantAdminRole) {
    return 'tenant_admin';
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

      // Actions
      login: (user: User, tokens: AuthTokens) => {
        const userRole = determineUserRole(user);
        const expiresAt = Date.now() + (tokens.expires_in * 1000);
        
        set({
          user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
          userRole,
          tokenExpiresAt: expiresAt,
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
        });
        // Clear localStorage
        localStorage.removeItem(TOKEN_STORAGE_KEY);
        localStorage.removeItem(USER_STORAGE_KEY);
      },

      setUser: (user: User) => {
        const userRole = determineUserRole(user);
        set({ user, userRole });
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
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) return true;
        
        // Check if token expires in the next 5 minutes (300,000 ms)
        return Date.now() >= (tokenExpiresAt - 300000);
      },

      getTimeUntilExpiry: () => {
        const { tokenExpiresAt } = get();
        if (!tokenExpiresAt) return 0;
        
        const timeLeft = tokenExpiresAt - Date.now();
        return Math.max(0, Math.floor(timeLeft / 1000)); // Return seconds
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
        userRole: state.userRole,
        tokenExpiresAt: state.tokenExpiresAt,
      }),
    }
  )
);