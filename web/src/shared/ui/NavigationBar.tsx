import { Link, NavLink } from "react-router-dom";
import type { ReactNode } from "react";

export interface NavItem {
  to: string;
  label: string;
  icon?: ReactNode;
}

export function NavigationBar({ items }: { items: NavItem[] }) {
  return (
    <header className="app-header">
      <Link to="/app" className="app-brand" aria-label="AIESEC Match, обзор">
        <span className="app-brand__mark">A</span>
        <span>AIESEC <strong>Match</strong></span>
      </Link>
      <nav className="ui-navbar" aria-label="Основная навигация">
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            end={it.to === "/"}
            className={({ isActive }) => `ui-navbar__item ${isActive ? "ui-navbar__item--active" : ""}`}
          >
            {it.icon && <span className="ui-navbar__icon" aria-hidden>{it.icon}</span>}
            <span className="ui-navbar__label">{it.label}</span>
          </NavLink>
        ))}
      </nav>
    </header>
  );
}