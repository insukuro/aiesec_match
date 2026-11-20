import type { MatchLabel as ML } from "../../shared/api/types";
import { Badge } from "../../shared/ui/Badge";

const MAP: Record<ML, { text: string; tone: "success" | "blue" | "warning" }> = {
  excellent: { text: "Отлично подходит", tone: "success" },
  good: { text: "Хорошо", tone: "blue" },
  fair: { text: "Средне", tone: "warning" },
};

export function MatchLabel({ label }: { label: ML | null | undefined }) {
  if (!label) return null;
  const m = MAP[label];
  if (!m) return null;
  return <Badge tone={m.tone}>{m.text}</Badge>;
}