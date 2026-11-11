import type { MatchLabel as ML } from "../../shared/api/types";
import { Badge } from "../../shared/ui/Badge";

const MAP: Record<ML, { text: string; tone: "success" | "blue" | "warning" }> = {
  excellent: { text: "Отлично подходит", tone: "success" },
  good: { text: "Хорошо", tone: "blue" },
  fair: { text: "Средне", tone: "warning" },
};

export function MatchLabel({ label }: { label: ML }) {
  const m = MAP[label];
  return <Badge tone={m.tone}>{m.text}</Badge>;
}