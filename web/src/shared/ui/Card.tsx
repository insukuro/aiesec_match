import type { HTMLAttributes, PropsWithChildren } from "react";

export function Card({ className = "", children, ...rest }: PropsWithChildren<HTMLAttributes<HTMLDivElement>>) {
  return <div className={`ui-card ${className}`} {...rest}>{children}</div>;
}