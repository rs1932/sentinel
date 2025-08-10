export { 
  TerminologyProvider, 
  useTerminologyContext, 
  useT 
} from './TerminologyProvider';

export { TerminologyWrapper } from './TerminologyWrapper';
export { TerminologyDemo } from './TerminologyDemo';

// Re-export hooks for convenience
export { useTerminology, useTranslation } from '@/hooks/useTerminology';

// Re-export service for advanced usage
export { terminologyService } from '@/lib/terminology-service';