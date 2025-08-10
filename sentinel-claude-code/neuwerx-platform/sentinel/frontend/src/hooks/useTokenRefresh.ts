import { useEffect, useRef } from 'react';
import { useAuthStore } from '@/store/auth';
import { apiClient } from '@/lib/api';

export function useTokenRefresh() {
  const { isAuthenticated, tokens, isTokenExpired, refreshToken, logout } = useAuthStore();
  const refreshTimeoutRef = useRef<NodeJS.Timeout>();

  useEffect(() => {
    if (!isAuthenticated || !tokens) {
      return;
    }

    // Set token in API client on mount
    apiClient.setToken(tokens.access_token);

    const scheduleRefresh = () => {
      // Clear existing timeout
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }

      // Check if token is expired or close to expiry
      if (isTokenExpired()) {
        // Try to refresh immediately
        refreshToken().catch(() => {
          // If refresh fails, user will be logged out by the store
          console.warn('Token refresh failed, user logged out');
        });
      } else {
        // Schedule refresh for 5 minutes before expiry
        const { tokenExpiresAt } = useAuthStore.getState();
        if (tokenExpiresAt) {
          const refreshTime = tokenExpiresAt - Date.now() - 300000; // 5 minutes before expiry
          const timeUntilRefresh = Math.max(refreshTime, 60000); // At least 1 minute from now

          refreshTimeoutRef.current = setTimeout(async () => {
            try {
              await refreshToken();
              scheduleRefresh(); // Schedule next refresh
            } catch (error) {
              console.error('Scheduled token refresh failed:', error);
            }
          }, timeUntilRefresh);
        }
      }
    };

    // Schedule initial refresh
    scheduleRefresh();

    // Cleanup timeout on unmount
    return () => {
      if (refreshTimeoutRef.current) {
        clearTimeout(refreshTimeoutRef.current);
      }
    };
  }, [isAuthenticated, tokens, isTokenExpired, refreshToken, logout]);

  // Also handle page focus to refresh if needed
  useEffect(() => {
    const handleFocus = () => {
      if (isAuthenticated && isTokenExpired()) {
        refreshToken().catch(() => {
          console.warn('Token refresh on focus failed');
        });
      }
    };

    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, [isAuthenticated, isTokenExpired, refreshToken]);
}