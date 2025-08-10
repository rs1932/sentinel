'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';

interface PageTransitionProps {
  children: React.ReactNode;
}

export function PageTransition({ children }: PageTransitionProps) {
  const [displayChildren, setDisplayChildren] = useState(children);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const pathname = usePathname();

  useEffect(() => {
    if (children !== displayChildren) {
      setIsTransitioning(true);
      
      const timer = setTimeout(() => {
        setDisplayChildren(children);
        setIsTransitioning(false);
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [children, displayChildren]);

  return (
    <div className={`transition-all duration-200 ease-in-out ${
      isTransitioning ? 'opacity-0 translate-y-1' : 'opacity-100 translate-y-0'
    }`}>
      {displayChildren}
    </div>
  );
}