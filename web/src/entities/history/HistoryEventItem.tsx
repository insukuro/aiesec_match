import { Link } from "react-router-dom";
import type { HistoryEvent } from "../../shared/api/types";
import { formatDateTime } from "../../shared/lib/date";

export function HistoryEventItem({ event }: { event: HistoryEvent }) {
  const relatedPath = event.type === "run_finished" && event.related_entity_id
    ? `/results?run=${encodeURIComponent(event.related_entity_id)}`
    : event.type.startsWith("signal_") && event.related_entity_id
      ? `/opportunity/${encodeURIComponent(event.related_entity_id)}`
      : null;
  return (
    <li className="ui-card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <strong>{event.title}</strong>
        <time className="muted" dateTime={event.occurred_at}>{formatDateTime(event.occurred_at)}</time>
      </div>
      {event.description && <div className="muted" style={{ marginTop: "var(--space-1)" }}>{event.description}</div>}
      {relatedPath && <Link to={relatedPath}>Открыть</Link>}
    </li>
  );
}