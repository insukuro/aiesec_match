import type { ReactNode } from "react";

export interface TimelineItem {
  id: string;
  icon?: ReactNode;
  title: string;
  occurredAt: string;
  description?: string;
  href?: string;
}

export function Timeline({ items, renderLink }: { items: TimelineItem[]; renderLink?: (item: TimelineItem, node: ReactNode) => ReactNode }) {
  return (
    <ol className="ui-timeline">
      {items.map((it) => {
        const content = (
          <>
            <div className="ui-timeline__head">
              <span className="ui-timeline__icon">{it.icon ?? "•"}</span>
              <span className="ui-timeline__title">{it.title}</span>
              <time className="ui-timeline__date" dateTime={it.occurredAt}>
                {new Date(it.occurredAt).toLocaleString("ru-RU")}
              </time>
            </div>
            {it.description && <div className="ui-timeline__body">{it.description}</div>}
          </>
        );
        return (
          <li key={it.id} className="ui-timeline__item">
            {renderLink && it.href ? renderLink(it, content) : content}
          </li>
        );
      })}
    </ol>
  );
}