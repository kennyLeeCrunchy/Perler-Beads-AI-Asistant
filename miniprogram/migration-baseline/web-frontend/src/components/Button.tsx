import type { ButtonHTMLAttributes, ReactNode } from 'react';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  icon?: ReactNode;
  fullWidth?: boolean;
}

export function Button({ variant = 'primary', icon, fullWidth, className = '', children, ...props }: ButtonProps) {
  return (
    <button className={`button button-${variant} ${fullWidth ? 'button-full' : ''} ${className}`} {...props}>
      {icon}
      <span>{children}</span>
    </button>
  );
}
