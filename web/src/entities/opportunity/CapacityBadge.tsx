import { pluralRu } from "../../shared/lib/format";

export function CapacityBadge({ capacity }: { capacity: { openings: number; available_openings: number; applicants_count: number } }) {
  return (
    <span className="muted" style={{ fontSize: "var(--fs-caption)" }}>
      Мест: {capacity.available_openings} из {capacity.openings} · {capacity.applicants_count}{" "}
      {pluralRu(capacity.applicants_count, ["заявка", "заявки", "заявок"])}
    </span>
  );
}