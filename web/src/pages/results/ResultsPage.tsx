import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { useCreateRecommendations } from "../../features/recommendations/useCreateRecommendations";
import { useAuth } from "../../features/auth/AuthContext";
import { ProfileSummaryBar } from "../../widgets/ProfileSummaryBar";
import { ResultsTabs } from "../../widgets/ResultsTabs";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Button } from "../../shared/ui/Button";
import { ApiError } from "../../shared/api/client";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";

export function ResultsPage() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const runId = searchParams.get("run");
  const toast = useToast();
  const { me } = useAuth();
  useEffect(() => { document.title = "Рекомендации — AIESEC Match"; }, []);

  const runQ = useQuery({
    queryKey: runId ? qk.runById(runId) : qk.run,
    queryFn: runId ? () => api.getRecommendation(runId) : fetchers.run,
    retry: (count, err) => (err instanceof ApiError && err.status === 404 ? false : count < 1),
  });
  const profileQ = useQuery({
    queryKey: qk.profile, queryFn: fetchers.profile, retry: 0,
  });
  const consentsQ = useQuery({ queryKey: qk.consents, queryFn: fetchers.consents, staleTime: 60_000 });
  const recalc = useCreateRecommendations();
  const currentPdConsent = consentsQ.data?.consents.find((consent) => consent.kind === "pd_processing");
  const hasCurrentPdConsent = Boolean(currentPdConsent && me?.consents.some(
    (consent) => consent.kind === currentPdConsent.kind && consent.version === currentPdConsent.version,
  ));
  const matchReady = Boolean(
    profileQ.data?.birth_date &&
    profileQ.data.study?.status &&
    profileQ.data.english_level &&
    (
      profileQ.data.programmes?.length ||
      profileQ.data.spheres?.length ||
      profileQ.data.activities?.length
    )
  );

  const handleMatchingError = (error: unknown) => {
    if (error instanceof ApiError && error.problem.type === "/problems/consent-required") {
      recalc.reset();
      void consentsQ.refetch();
      toast.show("Примите актуальное согласие в настройках, чтобы запустить подбор.", "info");
      nav(ROUTES.settings);
    }
  };

  const runMatching = () => {
    recalc.mutate(undefined, { onError: handleMatchingError });
  };

  const startMatching = () => {
    if (!matchReady) return;
    if (!consentsQ.data) return;
    if (!hasCurrentPdConsent) {
      nav(ROUTES.settings);
      return;
    }
    runMatching();
  };

  return (
    <main className="page">
      <h1 className="page__title">Рекомендации</h1>
      {profileQ.data && (
        <ProfileSummaryBar profile={profileQ.data} onEdit={() => nav(ROUTES.profileEdit)} />
      )}
      {profileQ.data && !matchReady && (
        <EmptyState
          title="Профиль нужно дополнить"
          description="Для подбора укажите дату рождения, статус обучения, английский, программы, сферы и активности."
          action={<Button onClick={() => nav(ROUTES.profileEdit)}>Дополнить профиль</Button>}
        />
      )}
      {runQ.isLoading && <Skeleton lines={6} />}
      {runQ.error && (runQ.error instanceof ApiError && runQ.error.status === 404 ? (
        <EmptyState
          title="Подборки пока нет"
          description="Запустите подбор, чтобы увидеть рекомендации"
          action={
            <Button onClick={startMatching} disabled={recalc.isPending || !matchReady || consentsQ.isLoading}>
              {recalc.isPending ? "Подбираем…" : "Подобрать"}
            </Button>
          }
        />
      ) : (
        <ErrorBanner error={runQ.error} onRetry={() => runQ.refetch()} />
      ))}
      {recalc.error && <ErrorBanner error={recalc.error} onRetry={startMatching} />}
      {runQ.data && (
        <>
          {runId && (
            <div className="row section">
              <Button variant="outline" onClick={() => nav(ROUTES.results, { replace: true })}>
                К последнему подбору
              </Button>
            </div>
          )}
          {runQ.data.degraded && (
            <div className="ui-badge" data-tone="warning">Часть рекомендаций недоступна</div>
          )}
          <ResultsTabs run={runQ.data} onOpenOpportunity={(id) => nav(ROUTES.opportunity(id))} />
          {!runId && <div className="row section">
            <Button variant="outline" onClick={startMatching} disabled={recalc.isPending || !matchReady || consentsQ.isLoading}>
              {recalc.isPending ? "Подбираем…" : "Подобрать заново"}
            </Button>
          </div>}
        </>
      )}
    </main>
  );
}