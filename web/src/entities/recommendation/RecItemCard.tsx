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
}

export function RecItemCard({ item, onOpen, onLike, onHide }: RecItemCardProps) {
  const o = item.opportunity;
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
        <Button size="sm" onClick={onOpen}>Подробнее</Button>
        <Button size="sm" variant="secondary" onClick={onLike}>Подходит</Button>
        <Button size="sm" variant="outline" onClick={onHide}>Скрыть</Button>
      </div>
    </article>
  );
}