import type { ButtonHTMLAttributes, ReactNode } from 'react';

export function IconButton({ children, className = '', ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { children: ReactNode }) {
  return <button className={`icon-button ${className}`} {...props}>{children}</button>;
}
