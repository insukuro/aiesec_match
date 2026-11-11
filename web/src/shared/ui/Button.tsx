import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

type Variant = "primary" | "secondary" | "outline" | "text" | "danger";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  block?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  block = false,
  className = "",
  type = "button",
  children,
  ...rest
}: PropsWithChildren<ButtonProps>) {
  return (
    <button
      type={type}
      data-variant={variant}
      data-size={size}
      data-block={block}
      className={`ui-btn ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}