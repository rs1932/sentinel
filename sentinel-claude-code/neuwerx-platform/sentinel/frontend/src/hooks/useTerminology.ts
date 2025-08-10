'use client';

import { useState, useEffect, useCallback } from 'react';
import { terminologyService } from '@/lib/terminology-service';
import type { TerminologyConfig, UpdateTerminologyRequest, TerminologyValidation } from '@/types';

/**
 * React hook for using the terminology service
 * 
 * Provides reactive access to tenant-specific terminology with automatic
 * updates when terminology changes. Includes methods for updating and
 * managing terminology configuration.
 * 
 * @param tenantId - The tenant ID to load terminology for (optional)
 * @returns Terminology state and management functions
 */
export function useTerminology(tenantId?: string) {
  const [terminology, setTerminology] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize terminology service when tenantId changes
  useEffect(() => {
    if (!tenantId) return;

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
    });

    return unsubscribe;
  }, []);

  /**
   * Translate a single term
   */
  const translate = useCallback((term: string): string => {
    return terminologyService.translate(term);
  }, [terminology]);

  /**
   * Translate multiple terms at once
   */
  const translateMultiple = useCallback((terms: string[]): Record<string, string> => {
    return terminologyService.translateMultiple(terms);
  }, [terminology]);

  /**
   * Get terminology configuration for a specific tenant
   */
  const getTerminology = useCallback(async (targetTenantId: string): Promise<TerminologyConfig> => {
    setLoading(true);
    setError(null);

    try {
      const config = await terminologyService.getTerminology(targetTenantId);
      return config;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch terminology';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Update terminology configuration
   */
  const updateTerminology = useCallback(async (
    targetTenantId: string,
    request: UpdateTerminologyRequest
  ): Promise<TerminologyConfig> => {
    setLoading(true);
    setError(null);

    try {
      const updatedConfig = await terminologyService.updateTerminology(targetTenantId, request);
      return updatedConfig;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update terminology';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Reset terminology to inherit from parent
   */
  const resetTerminology = useCallback(async (targetTenantId: string): Promise<TerminologyConfig> => {
    setLoading(true);
    setError(null);

    try {
      const resetConfig = await terminologyService.resetTerminology(targetTenantId);
      return resetConfig;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset terminology';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Apply terminology to child tenants
   */
  const applyToChildren = useCallback(async (
    targetTenantId: string,
    options: { terminology?: Record<string, string>; recursive?: boolean } = {}
  ): Promise<string[]> => {
    setLoading(true);
    setError(null);

    try {
      const affectedTenants = await terminologyService.applyToChildren(targetTenantId, options);
      return affectedTenants;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply terminology to children';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Validate terminology configuration
   */
  const validateTerminology = useCallback(async (
    terminologyConfig: Record<string, string>
  ): Promise<TerminologyValidation> => {
    try {
      return await terminologyService.validateTerminology(terminologyConfig);
    } catch (err) {
      console.error('Failed to validate terminology:', err);
      return {
        valid: false,
        errors: ['Failed to validate terminology'],
        warnings: [],
      };
    }
  }, []);

  /**
   * Get available industry templates
   */
  const getIndustryTemplates = useCallback(async (): Promise<Record<string, Record<string, string>>> => {
    setLoading(true);
    setError(null);

    try {
      const templates = await terminologyService.getIndustryTemplates();
      return templates;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch industry templates';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Apply an industry template
   */
  const applyTemplate = useCallback(async (
    targetTenantId: string,
    templateName: string,
    customizations?: Record<string, string>
  ): Promise<TerminologyConfig> => {
    setLoading(true);
    setError(null);

    try {
      const config = await terminologyService.applyTemplate(targetTenantId, templateName, customizations);
      return config;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to apply template';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    // Current terminology state
    terminology,
    loading,
    error,

    // Translation functions
    translate,
    translateMultiple,

    // Terminology management
    getTerminology,
    updateTerminology,
    resetTerminology,
    applyToChildren,
    validateTerminology,

    // Industry templates
    getIndustryTemplates,
    applyTemplate,

    // Utility
    clearError: () => setError(null),
  };
}

/**
 * Simple hook for just translation functionality
 * Use this when you only need to translate terms and don't need management functions
 */
export function useTranslation() {
  const [terminology, setTerminology] = useState<Record<string, string>>({});

  // Subscribe to terminology changes
  useEffect(() => {
    const unsubscribe = terminologyService.subscribe((newTerminology) => {
      setTerminology(newTerminology);
    });

    return unsubscribe;
  }, []);

  /**
   * Translate a single term
   */
  const t = useCallback((term: string): string => {
    return terminologyService.translate(term);
  }, [terminology]);

  /**
   * Translate multiple terms at once
   */
  const tMultiple = useCallback((terms: string[]): Record<string, string> => {
    return terminologyService.translateMultiple(terms);
  }, [terminology]);

  return {
    terminology,
    t,
    tMultiple,
  };
}