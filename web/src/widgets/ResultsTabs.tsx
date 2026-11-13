import { useState } from "react";
import type { ProgrammeKind, RecommendationRun } from "../shared/api/types";
import { Tabs } from "../shared/ui/Tabs";
import { RecItemCard } from "../entities/recommendation/RecItemCard";
import { EmptyState } from "../shared/ui/EmptyState";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../shared/config/brand";
import { useSendFeedback } from "../features/feedback/useSendFeedback";

function normalizePrior(value: unknown): ProgrammeKind[] {
  if (Array.isArray(value)) return value as ProgrammeKind[];
  if (value && typeof value === "object") return Object.keys(value) as ProgrammeKind[];
  return [];
}

export interface ResultsTabsProps {
  run: RecommendationRun;
  onOpenOpportunity: (id: number) => void;
}

export function ResultsTabs({ run, onOpenOpportunity }: ResultsTabsProps) {
  const prior = normalizePrior(run.programme_prior);
  const [active, setActive] = useState<ProgrammeKind | "">(prior[0] ?? "");
  const feedback = useSendFeedback();

  if (prior.length === 0) {
    return (
      <EmptyState
        title="Нет рекомендаций"
        description="Попробуйте изменить срок, страны или бюджет в профиле"
      />
    );
  }

  const items = prior.map((kind) => ({
    id: kind,
    label: PROGRAMME_LABEL[kind] ?? kind,
    color: PROGRAMME_COLORS[kind] ?? "#037EF3",
    badge: run.groups.find((g) => g.programme_kind === kind)?.items.length ?? 0,
  }));

  const group = run.groups.find((g) => g.programme_kind === active);

  return (
    <section>
      <Tabs items={items} active={active} onChange={(id) => setActive(id as ProgrammeKind)} />
      {(!group || group.items.length === 0) ? (
        <EmptyState
          title="Подходящих вакансий нет"
          description="Попробуйте изменить срок, страны или бюджет в профиле"
        />
      ) : (
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