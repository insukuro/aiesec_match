import type { ButtonHTMLAttributes } from "react";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
}

export function IconButton({ label, className = "", children, ...rest }: IconButtonProps) {
  return (
    <button type="button" aria-label={label} title={label} className={`ui-icon-btn ${className}`} {...rest}>
      {children}
    </button>
  );
}