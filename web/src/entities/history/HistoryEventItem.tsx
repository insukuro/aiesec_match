import type { HistoryEvent } from "../../shared/api/types";
import { formatDateTime } from "../../shared/lib/date";

export function HistoryEventItem({ event }: { event: HistoryEvent }) {
  return (
    <li className="ui-card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <strong>{event.title}</strong>
        <time className="muted" dateTime={event.occurred_at}>{formatDateTime(event.occurred_at)}</time>
      </div>
      {event.description && <div className="muted" style={{ marginTop: "var(--space-1)" }}>{event.description}</div>}
    </li>
  );
}