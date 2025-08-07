'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { ROUTES } from '@/constants';
import { Loader2 } from 'lucide-react';

interface AuthGuardProps {
  children: React.ReactNode;
}

export function AuthGuard({ children }: AuthGuardProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, user, setLoading } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    // Don't run auth checks until component is hydrated
    if (!isHydrated) return;

    const checkAuth = async () => {
      // Allow access to public routes
      const publicRoutes = ['/auth/login', '/auth/register', '/auth/forgot-password'];
      const isPublicRoute = publicRoutes.some(route => pathname.startsWith(route));

      if (isPublicRoute) {
        // If authenticated user tries to access login page, redirect to dashboard
        if (isAuthenticated && user) {
          router.replace(ROUTES.DASHBOARD);
        }
        setIsLoading(false);
        return;
      }

      // For protected routes, check authentication
      if (!isAuthenticated || !user) {
        router.replace(ROUTES.LOGIN);
        return;
      }

      setIsLoading(false);
    };

    checkAuth();
  }, [isAuthenticated, user, pathname, router, isHydrated]);

  // Show loading spinner while hydrating or checking authentication
  if (!isHydrated || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}