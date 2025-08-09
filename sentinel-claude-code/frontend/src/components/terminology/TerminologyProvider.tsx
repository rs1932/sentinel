'use client';

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { terminologyService } from '@/lib/terminology-service';

interface TerminologyContextType {
  terminology: Record<string, string>;
  loading: boolean;
  error: string | null;
  translate: (term: string) => string;
  translateMultiple: (terms: string[]) => Record<string, string>;
}

const TerminologyContext = createContext<TerminologyContextType | undefined>(undefined);

interface TerminologyProviderProps {
  children: ReactNode;
  tenantId?: string;
}

/**
 * Terminology Provider Component
 * 
 * Provides terminology context to all child components. Automatically
 * initializes the terminology service when a tenant is available and
 * provides reactive access to terminology changes throughout the component tree.
 * 
 * Usage:
 * ```tsx
 * <TerminologyProvider tenantId={currentUser?.tenant_id}>
 *   <App />
 * </TerminologyProvider>
 * ```
 */
export function TerminologyProvider({ children, tenantId }: TerminologyProviderProps) {
  const [terminology, setTerminology] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize terminology service when tenantId changes
  useEffect(() => {
    if (!tenantId) {
      // Clear terminology when no tenant is available (e.g., logged out)
      setTerminology({});
      setLoading(false);
      setError(null);
      return;
    }

    const initializeTerminology = async () => {
      setLoading(true);
      setError(null);

      try {
        await terminologyService.initialize(tenantId);
        setTerminology(terminologyService.getCurrentTerminology());
      } catch (err) {
        console.error('Failed to initialize terminology:', err);
        setError(err instanceof Error ? err.message : 'Failed to load terminology');
        // Set default terminology on error
        setTerminology(terminologyService.getCurrentTerminology());
      } finally {
        setLoading(false);
      }
    };

    initializeTerminology();
  }, [tenantId]);

  // Subscribe to terminology changes
  useEffect(() => {
    const unsubscribe = terminologyService.subscribe((newTerminology) => {
      setTerminology(newTerminology);
      setLoading(false);
      setError(null);
    });

    return unsubscribe;
  }, []);

  /**
   * Translate a single term
   */
  const translate = (term: string): string => {
    return terminologyService.translate(term);
  };

  /**
   * Translate multiple terms at once
   */
  const translateMultiple = (terms: string[]): Record<string, string> => {
    return terminologyService.translateMultiple(terms);
  };

  const contextValue: TerminologyContextType = {
    terminology,
    loading,
    error,
    translate,
    translateMultiple,
  };

  return (
    <TerminologyContext.Provider value={contextValue}>
      {children}
    </TerminologyContext.Provider>
  );
}

/**
 * Hook to use terminology context
 * 
 * Provides access to the terminology context. Must be used within a
 * TerminologyProvider component.
 * 
 * @returns Terminology context with translate functions and state
 */
export function useTerminologyContext(): TerminologyContextType {
  const context = useContext(TerminologyContext);
  
  if (context === undefined) {
    throw new Error('useTerminologyContext must be used within a TerminologyProvider');
  }
  
  return context;
}

// Export a simple translation hook for convenience
export function useT() {
  const { translate } = useTerminologyContext();
  return translate;
}

export default TerminologyProvider;