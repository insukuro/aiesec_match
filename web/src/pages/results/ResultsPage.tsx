import { useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { ProfileSummaryBar } from "../../widgets/ProfileSummaryBar";
import { ResultsTabs } from "../../widgets/ResultsTabs";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Button } from "../../shared/ui/Button";
import { ApiError } from "../../shared/api/client";
import { ROUTES } from "../../app/routes";

export function ResultsPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  useEffect(() => { document.title = "Рекомендации — AIESEC Match"; }, []);

  const runQ = useQuery({
    queryKey: qk.run,
    queryFn: fetchers.run,
    retry: (count, err) => (err instanceof ApiError && err.status === 404 ? false : count < 1),
  });
  const profileQ = useQuery({ queryKey: qk.profile, queryFn: fetchers.profile, retry: 0 });

  const recalc = useMutation({
    mutationFn: () => api.createRecommendations(crypto.randomUUID(), { mode: "sync", limit_per_programme: 10 }),
    onSuccess: (run) => qc.setQueryData(qk.run, run),
  });

  const content = useMemo(() => {
    if (runQ.isLoading) return <Skeleton lines={6} />;
    if (runQ.error) {
      if (runQ.error instanceof ApiError && runQ.error.status === 404) {
        return (
          <EmptyState
            title="Подборки пока нет"
            description="Запустите подбор, чтобы увидеть рекомендации"
            action={<Button onClick={() => recalc.mutate()} disabled={recalc.isPending}>Подобрать</Button>}
          />
        );
      }
      return <ErrorBanner error={runQ.error} onRetry={() => runQ.refetch()} />;
    }
    if (!runQ.data) return null;
    return (
      <>
        {runQ.data.degraded && (
          <div className="ui-badge" data-tone="warning">
            Часть рекомендаций недоступна
          </div>
        )}
        <ResultsTabs
          run={runQ.data}
          onOpenOpportunity={(id) => nav(ROUTES.opportunity(id))}
        />
      </>
    );
  }, [runQ, recalc, nav]);

  return (
    <main className="page">
      <h1 className="page__title">Рекомендации</h1>
      {profileQ.data && (
        <ProfileSummaryBar profile={profileQ.data} onEdit={() => nav(ROUTES.profileEdit)} />
      )}
      {content}
    </main>
  );
}