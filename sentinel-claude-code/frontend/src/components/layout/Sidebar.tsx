'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth';
import { NAVIGATION_MENUS } from '@/constants/navigation';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle } from '@/components/ui/sheet';
import { cn } from '@/lib/utils';
import { ChevronRight, X, ChevronLeft, Menu } from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { userRole } = useAuthStore();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    // Initialize from localStorage if available
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('sidebar-collapsed');
      return stored === 'true';
    }
    return false;
  });

  // Save collapsed state to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', isCollapsed.toString());
    // Clear expanded items when collapsing
    if (isCollapsed) {
      setExpandedItems([]);
    }
  }, [isCollapsed]);

  // Get navigation items based on user role
  const navigationItems = userRole ? NAVIGATION_MENUS[userRole] || [] : [];

  const toggleExpanded = (itemId: string) => {
    setExpandedItems(prev =>
      prev.includes(itemId)
        ? prev.filter(id => id !== itemId)
        : [...prev, itemId]
    );
  };

  const isItemActive = (path: string) => {
    return pathname === path || pathname.startsWith(path + '/');
  };

  const SidebarContent = ({ isMobile = false }) => (
    <div className="flex flex-col h-full">
      {/* Mobile header */}
      {isMobile && (
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold">Navigation</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Desktop minimize button */}
      {!isMobile && (
        <div className="flex items-center justify-between p-4 border-b">
          {!isCollapsed && <h2 className="text-lg font-semibold">Navigation</h2>}
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={cn("hover:bg-gray-100", isCollapsed && "mx-auto")}
          >
            {isCollapsed ? <Menu className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        </div>
      )}

      {/* Navigation items */}
      <nav className="flex-1 p-4 space-y-2">
        {navigationItems.map((item) => {
          const Icon = item.icon;
          const isActive = isItemActive(item.path);
          const hasChildren = item.children && item.children.length > 0;
          const isExpanded = expandedItems.includes(item.id);

          return (
            <div key={item.id}>
              {/* Main navigation item */}
              {hasChildren ? (
                <Button
                  variant="ghost"
                  className={cn(
                    'w-full h-10 px-3 font-normal',
                    isCollapsed ? 'justify-center' : 'justify-start text-left',
                    isActive
                      ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                  onClick={() => !isCollapsed && toggleExpanded(item.id)}
                  title={isCollapsed ? item.label : undefined}
                >
                  <Icon className={cn("h-4 w-4", !isCollapsed && "mr-3")} />
                  {!isCollapsed && (
                    <>
                      <span className="flex-1">{item.label}</span>
                      <ChevronRight
                        className={cn(
                          'h-4 w-4 transition-transform',
                          isExpanded && 'rotate-90'
                        )}
                      />
                    </>
                  )}
                </Button>
              ) : (
                <Link 
                  href={item.path}
                  prefetch={true}
                  onMouseEnter={() => {
                    // Prefetch on hover for faster navigation
                    router.prefetch(item.path);
                  }}
                  onClick={(e) => {
                    // Only close sidebar on mobile
                    if (isMobile) {
                      onClose();
                    }
                    // For desktop, do nothing - let navigation happen normally
                  }}
                >
                  <Button
                    variant="ghost"
                    className={cn(
                      'w-full h-10 px-3 font-normal transition-all duration-200',
                      isCollapsed ? 'justify-center' : 'justify-start text-left',
                      isActive
                        ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                        : 'text-gray-700 hover:bg-gray-100'
                    )}
                    title={isCollapsed ? item.label : undefined}
                  >
                    <Icon className={cn("h-4 w-4", !isCollapsed && "mr-3")} />
                    {!isCollapsed && item.label}
                  </Button>
                </Link>
              )}

              {/* Sub-navigation items - only show when not collapsed */}
              {hasChildren && isExpanded && !isCollapsed && (
                <div className="ml-6 mt-2 space-y-1">
                  {item.children?.map((subItem) => {
                    const SubIcon = subItem.icon;
                    const isSubActive = isItemActive(subItem.path);

                    return (
                      <Link 
                        key={subItem.id} 
                        href={subItem.path} 
                        onClick={(e) => {
                          // Only close sidebar on mobile
                          if (isMobile) {
                            onClose();
                          }
                        }}
                      >
                        <Button
                          variant="ghost"
                          className={cn(
                            'w-full justify-start h-9 px-3 text-sm font-normal',
                            isSubActive
                              ? 'bg-blue-50 text-blue-700 hover:bg-blue-100'
                              : 'text-gray-600 hover:bg-gray-100'
                          )}
                        >
                          <SubIcon className="mr-3 h-3 w-3" />
                          {subItem.label}
                        </Button>
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>

      {/* Footer info */}
      <div className="p-4 border-t bg-gray-50">
        {!isCollapsed ? (
          <div className="text-xs text-gray-500 space-y-1">
            <p>Role: {userRole?.replace('_', ' ').toUpperCase()}</p>
            <p>Version: 1.0.0</p>
          </div>
        ) : (
          <div className="text-xs text-gray-500 text-center">
            <p>v1.0</p>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className={cn(
        "hidden md:flex bg-white border-r border-gray-200 flex-col transition-all duration-300",
        isCollapsed ? "w-16" : "w-64"
      )}>
        <SidebarContent isMobile={false} />
      </aside>

      {/* Mobile sidebar */}
      <Sheet open={isOpen} onOpenChange={onClose}>
        <SheetContent side="left" className="w-64 p-0">
          <SidebarContent isMobile={true} />
        </SheetContent>
      </Sheet>
    </>
  );
}