import type { RecItem } from "../../shared/api/types";
import { MatchLabel } from "./MatchLabel";
import { ReasonList } from "./ReasonList";
import { ProgrammeBadge } from "../opportunity/ProgrammeBadge";
import { RequirementChips } from "../opportunity/RequirementChips";
import { CapacityBadge } from "../opportunity/CapacityBadge";
import { CostLabel } from "../opportunity/CostLabel";
import { Button } from "../../shared/ui/Button";

export interface RecItemCardProps {
  item: RecItem;
  onOpen: () => void;
  onLike: () => void;
  onHide: () => void;
  busy?: boolean;
}

export function RecItemCard({ item, onOpen, onLike, onHide, busy }: RecItemCardProps) {
  const o = item.opportunity;
  const liked = Boolean(item.liked);
  return (
    <article className="ui-card">
      <header className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <h3 style={{ margin: 0 }}>{o.title}</h3>
        <MatchLabel label={item.label} />
      </header>
      <div className="row" style={{ marginTop: "var(--space-1)" }}>
        <ProgrammeBadge kind={o.programme.kind} />
        <span className="muted">{o.place.country_name} · {o.place.lc_name}</span>
      </div>
      {o.organisation_name && <p className="muted" style={{ margin: 0 }}>{o.organisation_name}</p>}

      <div className="row" style={{ marginTop: "var(--space-2)" }}>
        <CostLabel cost={o.cost} />
        {o.duration_weeks != null && <span>{o.duration_weeks} нед.</span>}
        <CapacityBadge capacity={o.capacity} />
      </div>

      <RequirementChips requirements={o.requirements} />
      <ReasonList reasons={item.reasons} />

      <div className="row" style={{ marginTop: "var(--space-3)" }}>
        <Button size="sm" onClick={onOpen} disabled={busy}>Подробнее</Button>
        <Button size="sm" variant={liked ? "primary" : "secondary"} onClick={onLike} disabled={busy || liked}>
          {liked ? "♥ В избранном" : "Подходит"}
        </Button>
        <Button size="sm" variant="outline" onClick={onHide} disabled={busy}>Скрыть</Button>
      </div>
    </article>
  );
}