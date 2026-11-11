import { NavLink } from "react-router-dom";
import type { ReactNode } from "react";

export interface NavItem {
  to: string;
  label: string;
  icon: ReactNode;
}

export function NavigationBar({ items }: { items: NavItem[] }) {
  return (
    <nav className="ui-navbar" aria-label="Основная навигация">
      {items.map((it) => (
        <NavLink
          key={it.to}
          to={it.to}
          end={it.to === "/"}
          className={({ isActive }) => `ui-navbar__item ${isActive ? "ui-navbar__item--active" : ""}`}
        >
          <span className="ui-navbar__icon" aria-hidden>{it.icon}</span>
          <span className="ui-navbar__label">{it.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}