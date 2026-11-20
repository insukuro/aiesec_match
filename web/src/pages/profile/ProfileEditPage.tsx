import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { FormRenderer } from "../../features/questionnaire/FormRenderer";
import { Button } from "../../shared/ui/Button";
import { Skeleton } from "../../shared/ui/Skeleton";
import { useToast } from "../../shared/ui/Toast";
import { ROUTES } from "../../app/routes";
import { ApiError } from "../../shared/api/client";
import { errorMessage } from "../../shared/lib/errors";

export function ProfileEditPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const [stepIdx, setStepIdx] = useState(0);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    document.title = "Редактирование профиля — AIESEC Match";
    const beforeUnload = (e: BeforeUnloadEvent) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } };
    window.addEventListener("beforeunload", beforeUnload);
    return () => window.removeEventListener("beforeunload", beforeUnload);
  }, [dirty]);

  const schemaQ = useQuery({ queryKey: qk.formSchema, queryFn: fetchers.formSchema });
  const optionsQ = useQuery({ queryKey: qk.formOptions, queryFn: fetchers.formOptions });
  const profileQ = useQuery({ queryKey: qk.profile, queryFn: fetchers.profile, retry: 0 });

  const save = useMutation({
    mutationFn: async (body: unknown) => {
      const etag = profileQ.data ? `"${profileQ.data.profile_version}"` : undefined;
      return api.putProfile(body, etag);
    },
  });

  if (!schemaQ.data || !optionsQ.data || !profileQ.data) {
    return <main className="page"><Skeleton lines={6} /></main>;
  }
  const steps = schemaQ.data.steps.filter((step) => step.id !== "consent");
  const current = steps[stepIdx]!;
  const initial = profileQ.data as unknown as Record<string, unknown>;

  const persist = async (values: Record<string, unknown>) => {
    try {
      await save.mutateAsync(values);
      await qc.invalidateQueries({ queryKey: qk.profile });
      setDirty(false);
      toast.show("Профиль сохранён", "success");
    } catch (e) {
      if (e instanceof ApiError && e.status === 412) {
        toast.show("Профиль изменён в другом месте. Загрузите актуальный.", "error");
        await qc.invalidateQueries({ queryKey: qk.profile });
      } else {
        toast.show(errorMessage(e), "error");
      }
    }
  };

  return (
    <main className="page">
      <div className="form__progress">Шаг {stepIdx + 1} из {steps.length}</div>
      <FormRenderer
        step={current}
        options={optionsQ.data}
        initialValues={initial}
        onDirty={() => setDirty(true)}
        onNext={async (values) => {
          if (stepIdx + 1 < steps.length) {
            setStepIdx(stepIdx + 1);
          } else {
            await persist(values);
          }
        }}
        onBack={stepIdx > 0 ? () => setStepIdx(stepIdx - 1) : undefined}
      />
      <div className="row" style={{ marginTop: "var(--space-4)" }}>
        <Button variant="outline" onClick={() => nav(ROUTES.profile)} disabled={save.isPending}>
          Отменить изменения
        </Button>
      </div>
    </main>
  );
}