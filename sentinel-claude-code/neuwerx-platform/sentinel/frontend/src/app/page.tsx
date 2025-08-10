'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { ROUTES } from '@/constants';
import { Loader2 } from 'lucide-react';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, user, tokens, logout } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace(ROUTES.DASHBOARD);
    } else {
      router.replace(ROUTES.LOGIN);
    }
  }, [isAuthenticated, router]);

  // Debug - clear stale auth if needed
  const handleClearAuth = () => {
    logout();
    router.replace(ROUTES.LOGIN);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
        <p className="text-gray-600">Redirecting...</p>
        <div className="mt-4 text-sm text-gray-500">
          <p>Auth: {isAuthenticated ? 'Yes' : 'No'}</p>
          <p>User: {user ? user.email || 'Unknown' : 'None'}</p>
          <p>Tokens: {tokens ? 'Present' : 'None'}</p>
          <button 
            onClick={handleClearAuth}
            className="mt-2 px-3 py-1 bg-red-500 text-white rounded text-xs"
          >
            Clear Auth
          </button>
        </div>
      </div>
    </div>
  );
}
