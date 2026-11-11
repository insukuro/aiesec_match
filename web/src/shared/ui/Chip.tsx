import type { ButtonHTMLAttributes, PropsWithChildren } from "react";

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
  dot?: string;
}

export function Chip({ selected = false, dot, className = "", children, ...rest }: PropsWithChildren<ChipProps>) {
  return (
    <button type="button" className={`ui-chip ${selected ? "ui-chip--on" : ""} ${className}`} {...rest}>
      {dot && <span className="ui-chip__dot" style={{ background: dot }} aria-hidden />}
      {children}
    </button>
  );
}