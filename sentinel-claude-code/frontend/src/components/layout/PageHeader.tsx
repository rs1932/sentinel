'use client';

import { useT } from '@/components/terminology';

interface PageHeaderProps {
  title: string;
  description?: string;
  terminologyKey?: string; // Optional terminology key for translation
  actions?: React.ReactNode;
}

/**
 * PageHeader Component with Terminology Support
 * 
 * Provides a consistent page header with optional terminology translation.
 * If a terminologyKey is provided, it will translate the title using the
 * current tenant's terminology configuration.
 * 
 * Examples:
 * ```tsx
 * <PageHeader title="Users" terminologyKey="users" />
 * <PageHeader title="Tenant Management" terminologyKey="tenant_management" />
 * ```
 */
export function PageHeader({ 
  title, 
  description, 
  terminologyKey, 
  actions 
}: PageHeaderProps) {
  const t = useT();

  // Use translated title if terminology key is provided, otherwise use original title
  const displayTitle = terminologyKey ? t(terminologyKey) || title : title;

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{displayTitle}</h1>
        {description && (
          <p className="mt-1 text-sm text-gray-600">{description}</p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </div>
  );
}

export default PageHeader;