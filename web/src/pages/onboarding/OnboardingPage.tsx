import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { FormRenderer } from "../../features/questionnaire/FormRenderer";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { ROUTES } from "../../app/routes";
import { useToast } from "../../shared/ui/Toast";

export function OnboardingPage() {
  const { step } = useParams();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();

  useEffect(() => { document.title = "Анкета — AIESEC Match"; }, []);

  const idx = Number(step ?? "0");
  const schemaQ = useQuery({ queryKey: qk.formSchema, queryFn: fetchers.formSchema, staleTime: 5 * 60_000 });
  const optionsQ = useQuery({ queryKey: qk.formOptions, queryFn: fetchers.formOptions, staleTime: 5 * 60_000 });
  const profileQ = useQuery({ queryKey: qk.profile, queryFn: fetchers.profile, retry: 0 });

  const save = useMutation({
    mutationFn: (body: unknown) => api.putProfile(body, undefined),
  });

  const startRecommendations = useMutation({
    mutationFn: () => api.createRecommendations(crypto.randomUUID(), { mode: "sync", limit_per_programme: 10 }),
  });

  if (schemaQ.error) return <main className="page"><ErrorBanner error={schemaQ.error} onRetry={() => schemaQ.refetch()} /></main>;
  if (!schemaQ.data || !optionsQ.data) return <main className="page"><Skeleton lines={6} /></main>;
  const schema = schemaQ.data;
  if (idx >= schema.steps.length) { nav(ROUTES.results); return null; }
  const current = schema.steps[idx]!;

  const initial: Record<string, unknown> = (profileQ.data as unknown as Record<string, unknown>) ?? {};

  const onNext = async (values: Record<string, unknown>) => {
    try {
      await save.mutateAsync(values);
      await qc.invalidateQueries({ queryKey: qk.profile });
      if (idx + 1 < schema.steps.length) {
        nav(ROUTES.onboarding(idx + 1));
      } else {
        await startRecommendations.mutateAsync();
        await qc.invalidateQueries({ queryKey: qk.run });
        toast.show("Подборка готова", "success");
        nav(ROUTES.results);
      }
    } catch (e) {
      toast.show(e instanceof Error ? e.message : "Не удалось сохранить", "error");
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
      {idx > 0 && (
        <Button variant="text" onClick={() => nav(ROUTES.onboarding(idx - 1))}>Назад</Button>
      )}
    </main>
  );
}