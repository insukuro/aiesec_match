import { useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { FormRenderer } from "../../features/questionnaire/FormRenderer";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";
import { getPath } from "../../shared/lib/get";
import { useAuth } from "../../features/auth/AuthContext";

export function OnboardingPage() {
  const { step } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const { state, isGuest, refreshMe } = useAuth();

  useEffect(() => { document.title = "Анкета — AIESEC Match"; }, []);

  useEffect(() => {
    if (state.status === "unknown") nav(ROUTES.welcome, { replace: true });
    if (isGuest) nav(ROUTES.login, { replace: true });
  }, [state.status, isGuest, nav]);

  const idx = Number(step ?? "0");
  const schemaQ = useQuery({ queryKey: qk.formSchema, queryFn: fetchers.formSchema, staleTime: 5 * 60_000 });
  const optionsQ = useQuery({ queryKey: qk.formOptions, queryFn: fetchers.formOptions, staleTime: 5 * 60_000 });
  const profileQ = useQuery({
    queryKey: qk.profile, queryFn: fetchers.profile, retry: 0,
    enabled: !isGuest,
  });

  const saveProfile = useMutation({ mutationFn: (body: unknown) => api.putProfile(body) });

  const initial = useMemo<Record<string, unknown>>(
    () => (profileQ.data as unknown as Record<string, unknown>) ?? {},
    [profileQ.data],
  );

  if (schemaQ.error) return <main className="page"><ErrorBanner error={schemaQ.error} onRetry={() => schemaQ.refetch()} /></main>;
  if (!schemaQ.data || !optionsQ.data) return <main className="page"><Skeleton lines={6} /></main>;
  const schema = schemaQ.data;
  if (idx >= schema.steps.length) { nav(ROUTES.results, { replace: true }); return null; }
  const current = schema.steps[idx]!;

  const onNext = async (values: Record<string, unknown>) => {
    try {
      if (current.id === "consent") {
        const pd = getPath(values, "consent.pd_processing") === true;
        if (!pd) { toast.show("Нужно согласие на обработку данных", "error"); return; }
        await api.postConsent("pd_processing", "1.0");
        if (getPath(values, "consent.marketing") === true) await api.postConsent("marketing", "1.0");
        await refreshMe();
      } else if (current.id === "final") {
        await api.createRecommendations(crypto.randomUUID(), { mode: "sync", limit_per_programme: 10 });
        await qc.invalidateQueries({ queryKey: qk.run });
        toast.show("Подборка готова", "success");
        nav(ROUTES.results);
        return;
      } else {
        await saveProfile.mutateAsync(values);
        await qc.invalidateQueries({ queryKey: qk.profile });
      }
      if (idx + 1 < schema.steps.length) nav(ROUTES.onboarding(idx + 1));
    } catch (e) {
      toast.show(errorMessage(e), "error");
    }
  };

  return (
    <main className="page">
      <div className="form__progress">Шаг {idx + 1} из {schema.steps.length}</div>
      <FormRenderer
        step={current}
        options={optionsQ.data}
        initialValues={initial}
        onNext={onNext}
        onBack={idx > 0 ? () => nav(ROUTES.onboarding(idx - 1)) : undefined}
      />
    </main>
  );
}