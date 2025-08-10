'use client';

import { useState, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { useTokenRefresh } from '@/hooks/useTokenRefresh';
import { AppHeader } from './AppHeader';
import { Sidebar } from './Sidebar';
import { Loader2 } from 'lucide-react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isNavigating, setIsNavigating] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);
  const { isAuthenticated, user } = useAuthStore();
  const pathname = usePathname();
  
  // Handle hydration
  useEffect(() => {
    setIsHydrated(true);
  }, []);
  
  // Initialize token refresh mechanism
  useTokenRefresh();

  // Close sidebar when screen size changes to desktop
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768) {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Handle navigation loading state
  useEffect(() => {
    setIsNavigating(true);
    const timer = setTimeout(() => {
      setIsNavigating(false);
    }, 150); // Short delay to show loading state

    return () => clearTimeout(timer);
  }, [pathname]);

  const handleMenuToggle = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const handleSidebarClose = () => {
    setIsSidebarOpen(false);
  };

  // Don't render layout if not hydrated yet or not authenticated
  if (!isHydrated) {
    return <div className="flex-1">{children}</div>;
  }

  if (!isAuthenticated || !user) {
    return <div className="flex-1">{children}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* App Header */}
      <AppHeader onMenuToggle={handleMenuToggle} />
      
      <div className="flex h-[calc(100vh-64px)]">
        {/* Sidebar */}
        <Sidebar isOpen={isSidebarOpen} onClose={handleSidebarClose} />
        
        {/* Main content area */}
        <main className="flex-1 overflow-auto relative">
          {/* Loading overlay */}
          {isNavigating && (
            <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center">
              <div className="flex items-center space-x-2 text-blue-600">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm font-medium">Loading...</span>
              </div>
            </div>
          )}
          
          {/* Content with smooth transition */}
          <div className={`p-6 transition-opacity duration-200 ${isNavigating ? 'opacity-50' : 'opacity-100'}`}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}