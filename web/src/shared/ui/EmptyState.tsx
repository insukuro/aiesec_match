import type { ReactNode } from "react";

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="ui-empty" role="status">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && <div className="ui-empty__action">{action}</div>}
    </div>
  );
}