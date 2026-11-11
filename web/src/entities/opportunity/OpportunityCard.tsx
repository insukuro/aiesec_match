import type { OpportunityCard as OpportunityCardData } from "../../shared/api/types";
import { ProgrammeBadge } from "./ProgrammeBadge";
import { RequirementChips } from "./RequirementChips";
import { CapacityBadge } from "./CapacityBadge";
import { CostLabel } from "./CostLabel";

export function OpportunityCard({ card, onOpen }: { card: OpportunityCardData; onOpen?: () => void }) {
  return (
    <article className="ui-card">
      <header className="row" style={{ justifyContent: "space-between", alignItems: "flex-start" }}>
        <h3 style={{ margin: 0 }}>{card.title}</h3>
        <ProgrammeBadge kind={card.programme.kind} />
      </header>
      <p className="muted" style={{ marginTop: "var(--space-1)" }}>
        {card.place.country_name} · {card.place.lc_name}
      </p>
      <div className="row" style={{ marginTop: "var(--space-2)" }}>
        <CostLabel cost={card.cost} />
        {card.duration_weeks != null && <span>{card.duration_weeks} нед.</span>}
        <CapacityBadge capacity={card.capacity} />
      </div>
      <RequirementChips requirements={card.requirements} />
      {onOpen && (
        <div className="row" style={{ marginTop: "var(--space-3)" }}>
          <button type="button" className="ui-btn" data-variant="secondary" data-size="sm" onClick={onOpen}>Подробнее</button>
        </div>
      )}
    </article>
  );
}