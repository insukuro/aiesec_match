import type { ReactNode } from "react";

export interface TabItem {
  id: string;
  label: string;
  badge?: ReactNode;
  color?: string;
}

export interface TabsProps {
  items: TabItem[];
  active: string;
  onChange: (id: string) => void;
}

export function Tabs({ items, active, onChange }: TabsProps) {
  return (
    <div role="tablist" className="ui-tabs">
      {items.map((t) => (
        <button
          key={t.id}
          role="tab"
          type="button"
          aria-selected={active === t.id}
          className={active === t.id ? "ui-tabs__tab ui-tabs__tab--on" : "ui-tabs__tab"}
          style={t.color ? { ["--tab-color" as string]: t.color } : undefined}
          onClick={() => onChange(t.id)}
        >
          {t.label}
          {t.badge != null && <span className="ui-tabs__badge">{t.badge}</span>}
        </button>
      ))}
    </div>
  );
}