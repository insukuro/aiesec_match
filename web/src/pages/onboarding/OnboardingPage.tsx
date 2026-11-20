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
import { useAuth } from "../../features/auth/AuthContext";
import { ApiError } from "../../shared/api/client";
import { ConsentSettings } from "../../features/consent/ConsentSettings";

export function OnboardingPage() {
  const { step } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const { state, me, refreshMe } = useAuth();

  useEffect(() => { document.title = "Анкета — AIESEC Match"; }, []);

  useEffect(() => {
    if (state.status === "unknown") nav(ROUTES.welcome, { replace: true });
  }, [state.status, nav]);

  const idx = Number(step ?? "0");
  const schemaQ = useQuery({ queryKey: qk.formSchema, queryFn: fetchers.formSchema, staleTime: 5 * 60_000 });
  const optionsQ = useQuery({ queryKey: qk.formOptions, queryFn: fetchers.formOptions, staleTime: 5 * 60_000 });
  const consentsQ = useQuery({ queryKey: qk.consents, queryFn: fetchers.consents, staleTime: 60_000 });
  const profileQ = useQuery({
    queryKey: qk.profile, queryFn: fetchers.profile, retry: 0,
  });

  const saveProfile = useMutation({ mutationFn: (body: unknown) => api.putProfile(body) });

  const initial = useMemo<Record<string, unknown>>(
    () => (profileQ.data as unknown as Record<string, unknown>) ?? {},
    [profileQ.data],
  );

  if (consentsQ.error) {
    return <main className="page"><ErrorBanner error={consentsQ.error} onRetry={() => consentsQ.refetch()} /></main>;
  }
  if (!consentsQ.data || !me) return <main className="page"><Skeleton lines={6} /></main>;
  const needsRequiredConsent = consentsQ.data.consents.some((document) =>
    document.required && !me.consents.some(
      (consent) => consent.kind === document.kind && consent.version === document.version,
    ),
  );
  if (needsRequiredConsent) {
    return (
      <main className="page">
        <h1 className="page__title">Перед продолжением примите актуальные согласия</h1>
        <ConsentSettings acceptedConsents={me.consents} refreshMe={refreshMe} />
      </main>
    );
  }
  if (schemaQ.error) return <main className="page"><ErrorBanner error={schemaQ.error} onRetry={() => schemaQ.refetch()} /></main>;
  const profileNotFound = profileQ.error instanceof ApiError && profileQ.error.status === 404;
  if (profileQ.error && !profileNotFound) {
    return <main className="page"><ErrorBanner error={profileQ.error} onRetry={() => profileQ.refetch()} /></main>;
  }
  if (!schemaQ.data || !optionsQ.data || profileQ.isLoading) {
    return <main className="page"><Skeleton lines={6} /></main>;
  }
  const steps = schemaQ.data.steps;
  if (idx >= steps.length) { nav(ROUTES.dashboard, { replace: true }); return null; }
  const current = steps[idx]!;

  const onNext = async (values: Record<string, unknown>) => {
    try {
      await saveProfile.mutateAsync(values);
      await qc.invalidateQueries({ queryKey: qk.profile });
      if (current.id === "final") {
        await refreshMe();
        nav(ROUTES.dashboard, { replace: true });
        return;
      }
      if (idx + 1 < steps.length) nav(ROUTES.onboarding(idx + 1));
    } catch (e) {
      toast.show(errorMessage(e), "error");
    }
  };

  return (
    <main className="page">
      <div className="form__progress">Шаг {idx + 1} из {steps.length}</div>
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