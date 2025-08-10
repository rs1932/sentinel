'use client';

import { useAuthStore } from '@/store/auth';
import { TerminologyProvider } from './TerminologyProvider';
import { ReactNode } from 'react';

interface TerminologyWrapperProps {
  children: ReactNode;
}

/**
 * TerminologyWrapper Component
 * 
 * Wraps the TerminologyProvider with authentication context.
 * Automatically provides the current user's tenant_id to the
 * TerminologyProvider for proper terminology initialization.
 */
export function TerminologyWrapper({ children }: TerminologyWrapperProps) {
  const { user } = useAuthStore();
  
  // Get tenant ID from the authenticated user
  const tenantId = user?.tenant_id;

  return (
    <TerminologyProvider tenantId={tenantId}>
      {children}
    </TerminologyProvider>
  );
}

export default TerminologyWrapper;