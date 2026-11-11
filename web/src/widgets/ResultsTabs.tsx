import { useState } from "react";
import type { RecommendationRun } from "../shared/api/types";
import { Tabs } from "../shared/ui/Tabs";
import { RecItemCard } from "../entities/recommendation/RecItemCard";
import { EmptyState } from "../shared/ui/EmptyState";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../shared/config/brand";
import { useSendFeedback } from "../features/feedback/useSendFeedback";

export interface ResultsTabsProps {
  run: RecommendationRun;
  onOpenOpportunity: (id: number) => void;
}

export function ResultsTabs({ run, onOpenOpportunity }: ResultsTabsProps) {
  const [active, setActive] = useState<string>(run.programme_prior[0] ?? "");
  const feedback = useSendFeedback();
  if (run.programme_prior.length === 0) return <EmptyState title="Нет рекомендаций" />;

  const items = run.programme_prior.map((kind) => ({
    id: kind,
    label: PROGRAMME_LABEL[kind],
    color: PROGRAMME_COLORS[kind],
    badge: run.groups.find((g) => g.programme_kind === kind)?.items.length ?? 0,
  }));

  const group = run.groups.find((g) => g.programme_kind === active);

  return (
    <section>
      <Tabs items={items} active={active} onChange={setActive} />
      {group && group.items.length === 0 && (
        <EmptyState
          title="Подходящих вакансий нет"
          description="Попробуйте изменить срок, страны или бюджет в профиле"
        />
      )}
      {group && group.items.length > 0 && (
        <ul className="stack" style={{ listStyle: "none", padding: 0, marginTop: "var(--space-3)" }}>
          {group.items.map((item) => (
            <li key={item.opportunity.opportunity_id}>
              <RecItemCard
                item={item}
                onOpen={() => onOpenOpportunity(item.opportunity.opportunity_id)}
                onLike={() => feedback.mutate({ opportunity_id: item.opportunity.opportunity_id, signal: "liked" })}
                onHide={() => feedback.mutate({ opportunity_id: item.opportunity.opportunity_id, signal: "hidden" })}
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}