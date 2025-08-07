'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { toast } from '@/hooks/use-toast';
import { apiClient } from '@/lib/api';

interface User {
  id: string;
  email: string;
  username?: string;
  is_active: boolean;
}

interface BulkOperationsContextType {
  selectedUsers: User[];
  isSelecting: boolean;
  selectUser: (user: User) => void;
  deselectUser: (userId: string) => void;
  selectAll: (users: User[]) => void;
  clearSelection: () => void;
  toggleSelecting: () => void;
  performBulkAction: (action: string, userIds: string[]) => Promise<void>;
}

const BulkOperationsContext = createContext<BulkOperationsContextType | undefined>(undefined);

export function useBulkOperations() {
  const context = useContext(BulkOperationsContext);
  if (!context) {
    throw new Error('useBulkOperations must be used within a BulkOperationsProvider');
  }
  return context;
}

interface BulkOperationsProviderProps {
  children: ReactNode;
  onRefresh?: () => void;
}

export function BulkOperationsProvider({ children, onRefresh }: BulkOperationsProviderProps) {
  const [selectedUsers, setSelectedUsers] = useState<User[]>([]);
  const [isSelecting, setIsSelecting] = useState(false);

  const selectUser = useCallback((user: User) => {
    setSelectedUsers(prev => {
      const exists = prev.find(u => u.id === user.id);
      if (exists) {
        return prev; // Already selected
      }
      return [...prev, user];
    });
  }, []);

  const deselectUser = useCallback((userId: string) => {
    setSelectedUsers(prev => prev.filter(u => u.id !== userId));
  }, []);

  const selectAll = useCallback((users: User[]) => {
    setSelectedUsers(users);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedUsers([]);
    setIsSelecting(false);
  }, []);

  const toggleSelecting = useCallback(() => {
    setIsSelecting(prev => !prev);
    if (isSelecting) {
      setSelectedUsers([]);
    }
  }, [isSelecting]);

  const performBulkAction = useCallback(async (action: string, userIds: string[]) => {
    try {
      let endpoint = '';
      let method = 'POST';
      let body: any = { user_ids: userIds };

      switch (action) {
        case 'activate':
          endpoint = '/users/bulk/activate';
          break;
        case 'deactivate':
          endpoint = '/users/bulk/deactivate';
          break;
        case 'delete':
          endpoint = '/users/bulk/delete';
          method = 'DELETE';
          break;
        default:
          throw new Error(`Unknown bulk action: ${action}`);
      }

      const response = await apiClient.request(endpoint, {
        method,
        body: JSON.stringify(body),
      });

      // Show success toast with details
      const successCount = response.successful || response.success_count || userIds.length;
      const failureCount = response.failed || response.failure_count || 0;
      
      let message = `${successCount} user${successCount !== 1 ? 's' : ''} ${action}d successfully`;
      if (failureCount > 0) {
        message += `, ${failureCount} failed`;
      }

      toast({
        title: 'Bulk Operation Complete',
        description: message,
      });

      // Clear selection and refresh
      clearSelection();
      onRefresh?.();

      return response;
    } catch (error: any) {
      console.error('Bulk operation failed:', error);
      
      toast({
        title: 'Bulk Operation Failed',
        description: error.message || `Failed to ${action} users`,
        variant: 'destructive',
      });
      
      throw error;
    }
  }, [clearSelection, onRefresh]);

  const contextValue: BulkOperationsContextType = {
    selectedUsers,
    isSelecting,
    selectUser,
    deselectUser,
    selectAll,
    clearSelection,
    toggleSelecting,
    performBulkAction,
  };

  return (
    <BulkOperationsContext.Provider value={contextValue}>
      {children}
    </BulkOperationsContext.Provider>
  );
}