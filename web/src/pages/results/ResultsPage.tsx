import { useEffect } from "react";
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
import { GuestBanner } from "../../widgets/GuestBanner";
import { useAuth } from "../../features/auth/AuthContext";

export function ResultsPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const { isGuest } = useAuth();
  useEffect(() => { document.title = "Рекомендации — AIESEC Match"; }, []);

  const runQ = useQuery({
    queryKey: qk.run,
    queryFn: fetchers.run,
    retry: (count, err) => (err instanceof ApiError && err.status === 404 ? false : count < 1),
    enabled: !isGuest,
  });
  const profileQ = useQuery({
    queryKey: qk.profile, queryFn: fetchers.profile, retry: 0, enabled: !isGuest,
  });

  const recalc = useMutation({
    mutationFn: () => api.createRecommendations(crypto.randomUUID(), { mode: "sync", limit_per_programme: 10 }),
    onSuccess: (run) => qc.setQueryData(qk.run, run),
  });

  if (isGuest) {
    return (
      <main className="page">
        <h1 className="page__title">Рекомендации</h1>
        <GuestBanner />
        <EmptyState
          title="Создайте аккаунт"
          description="Профиль, история и персональные подборки доступны только в аккаунте."
          action={<Button onClick={() => nav(ROUTES.register)}>Создать аккаунт</Button>}
        />
      </main>
    );
  }

  return (
    <main className="page">
      <h1 className="page__title">Рекомендации</h1>
      {profileQ.data && (
        <ProfileSummaryBar profile={profileQ.data} onEdit={() => nav(ROUTES.profileEdit)} />
      )}
      {runQ.isLoading && <Skeleton lines={6} />}
      {runQ.error && (runQ.error instanceof ApiError && runQ.error.status === 404 ? (
        <EmptyState
          title="Подборки пока нет"
          description="Запустите подбор, чтобы увидеть рекомендации"
          action={
            <Button onClick={() => recalc.mutate()} disabled={recalc.isPending}>
              {recalc.isPending ? "Подбираем…" : "Подобрать"}
            </Button>
          }
        />
      ) : (
        <ErrorBanner error={runQ.error} onRetry={() => runQ.refetch()} />
      ))}
      {runQ.data && (
        <>
          {runQ.data.degraded && (
            <div className="ui-badge" data-tone="warning">Часть рекомендаций недоступна</div>
          )}
          <ResultsTabs run={runQ.data} onOpenOpportunity={(id) => nav(ROUTES.opportunity(id))} />
        </>
      )}
    </main>
  );
}