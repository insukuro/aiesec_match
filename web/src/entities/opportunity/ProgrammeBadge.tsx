import type { ProgrammeKind } from "../../shared/api/types";
import { Badge } from "../../shared/ui/Badge";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../../shared/config/brand";

export function ProgrammeBadge({ kind }: { kind: ProgrammeKind }) {
  return <Badge tone="programme" style={{ background: PROGRAMME_COLORS[kind], color: "#fff" }}>{PROGRAMME_LABEL[kind]}</Badge>;
}