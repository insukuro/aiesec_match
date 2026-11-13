import type { PropsWithChildren, ReactNode } from "react";

export interface AuthCardProps {
  title: string;
  subtitle?: string;
  footer?: ReactNode;
}

export function AuthCard({ title, subtitle, footer, children }: PropsWithChildren<AuthCardProps>) {
  return (
    <main className="page page--narrow">
      <header className="auth-card__header">
        <h1 className="page__title">{title}</h1>
        {subtitle && <p className="muted">{subtitle}</p>}
      </header>
      <div className="ui-card auth-card__body">{children}</div>
      {footer && <div className="auth-card__footer">{footer}</div>}
    </main>
  );
}