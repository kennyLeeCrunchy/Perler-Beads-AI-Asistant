import type { ReactNode } from 'react';

export function ResponsivePageContainer({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`page-container ${className}`}>{children}</div>;
}
