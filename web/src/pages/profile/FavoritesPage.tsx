import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import { Tabs } from "../../shared/ui/Tabs";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { EmptyState } from "../../shared/ui/EmptyState";
import { OpportunityCard } from "../../entities/opportunity/OpportunityCard";
import { useRemoveFeedback } from "../../features/feedback/useSendFeedback";
import { ROUTES } from "../../app/routes";

type TabId = "liked" | "hidden";

export function FavoritesPage() {
  const nav = useNavigate();
  const [tab, setTab] = useState<TabId>("liked");
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => { document.title = "Избранное — AIESEC Match"; }, []);

  const q = useQuery({
    queryKey: tab === "liked" ? qk.liked({ limit, offset }) : qk.hidden({ limit, offset }),
    queryFn: () =>
      tab === "liked"
        ? api.getLikedFeedback({ limit, offset })
        : api.getHiddenFeedback({ limit, offset }),
  });

  const remove = useRemoveFeedback();

  return (
    <main className="page">
      <Button variant="text" onClick={() => nav(ROUTES.profile)}>← Назад в профиль</Button>
      <h1 className="page__title">Избранное</h1>

      <Tabs
        items={[
          { id: "liked", label: "♥ Избранное" },
          { id: "hidden", label: "👁 Скрытые" },
        ]}
        active={tab}
        onChange={(id) => { setTab(id as TabId); setOffset(0); }}
      />

      {q.isLoading && <Skeleton lines={6} />}
      {q.error && <ErrorBanner error={q.error} onRetry={() => q.refetch()} />}
      {q.data && q.data.items.length === 0 && (
        <EmptyState
          title={tab === "liked" ? "Нет избранных вакансий" : "Нет скрытых вакансий"}
          description={
            tab === "liked"
              ? "Отмечайте «Подходит» в рекомендациях — вакансии появятся здесь."
              : "Скрытые вакансии не попадают в подборки. Вернуть их можно здесь."
          }
        />
      )}
      {q.data && q.data.items.length > 0 && (
        <ul className="stack" style={{ listStyle: "none", padding: 0, marginTop: "var(--space-3)" }}>
          {q.data.items.map((card) => (
            <li key={card.opportunity_id}>
              <OpportunityCard
                card={card}
                onOpen={() => nav(ROUTES.opportunity(card.opportunity_id))}
              />
              <div className="row" style={{ marginTop: "var(--space-2)" }}>
                {tab === "liked" ? (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={remove.isPending}
                    onClick={() => remove.mutate({ id: card.opportunity_id, signal: "liked" })}
                  >
                    Убрать из избранного
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={remove.isPending}
                    onClick={() => remove.mutate({ id: card.opportunity_id, signal: "hidden" })}
                  >
                    Вернуть в рекомендации
                  </Button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      {q.data && q.data.total > limit && (
        <div className="row" style={{ justifyContent: "center", marginTop: "var(--space-4)" }}>
          <Button variant="outline" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Назад</Button>
          <span className="muted">{offset + 1}–{Math.min(offset + limit, q.data.total)} из {q.data.total}</span>
          <Button variant="outline" disabled={offset + limit >= q.data.total} onClick={() => setOffset(offset + limit)}>Далее</Button>
        </div>
      )}
    </main>
  );
}