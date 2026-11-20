import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import type { ConsentKind, Me } from "../../shared/api/types";
import { Button } from "../../shared/ui/Button";
import { Dialog } from "../../shared/ui/Dialog";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";

export function ConsentSettings({
  acceptedConsents,
  refreshMe,
}: {
  acceptedConsents: Me["consents"];
  refreshMe: () => Promise<void>;
}) {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [confirmMarketingRevoke, setConfirmMarketingRevoke] = useState(false);
  const documents = useQuery({
    queryKey: qk.consents,
    queryFn: fetchers.consents,
  });
  const accept = useMutation({
    mutationFn: ({ kind, version }: { kind: ConsentKind; version: string }) =>
      api.postConsent(kind, version),
    onSuccess: async () => {
      await refreshMe();
      toast.show("Согласие сохранено", "success");
    },
    onError: (error) => {
      void queryClient.invalidateQueries({ queryKey: qk.consents });
      toast.show(errorMessage(error), "error");
    },
  });
  const revokeMarketing = useMutation({
    mutationFn: () => api.revokeConsent("marketing"),
    onSuccess: async () => {
      await refreshMe();
      setConfirmMarketingRevoke(false);
      toast.show("Согласие на новости отозвано", "success");
    },
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  return (
    <section className="section">
      <h2 className="section__title">Согласия</h2>
      {documents.isLoading && <Skeleton lines={4} />}
      {documents.error && (
        <ErrorBanner error={documents.error} onRetry={() => documents.refetch()} />
      )}
      {documents.data?.consents.map((document) => {
        const acceptedCurrent = acceptedConsents.some(
          (consent) => consent.kind === document.kind && consent.version === document.version,
        );
        const acceptedBefore = acceptedConsents.some((consent) => consent.kind === document.kind);

        return (
          <article className="ui-card stack" key={document.kind}>
            <div>
              <h3>{document.title}</h3>
              <p>{document.text}</p>
              <p className="muted">Версия {document.version}</p>
            </div>
            <p className="muted" role="status">
              {acceptedCurrent
                ? "Актуальная версия принята."
                : acceptedBefore
                  ? "Появилась новая версия — её нужно принять."
                  : document.required
                    ? "Это согласие необходимо для работы персонального подбора."
                    : "Согласие не предоставлено."}
            </p>
            {!acceptedCurrent && (
              <Button
                variant="outline"
                disabled={accept.isPending}
                onClick={() => accept.mutate({ kind: document.kind, version: document.version })}
              >
                Принять версию {document.version}
              </Button>
            )}
            {document.kind === "marketing" && acceptedBefore && (
              <Button variant="text" onClick={() => setConfirmMarketingRevoke(true)}>
                Отозвать согласие
              </Button>
            )}
          </article>
        );
      })}
      <Dialog
        open={confirmMarketingRevoke}
        title="Отозвать согласие на новости?"
        onClose={() => setConfirmMarketingRevoke(false)}
        footer={
          <>
            <Button variant="outline" onClick={() => setConfirmMarketingRevoke(false)}>
              Отмена
            </Button>
            <Button
              variant="danger"
              disabled={revokeMarketing.isPending}
              onClick={() => revokeMarketing.mutate()}
            >
              Отозвать
            </Button>
          </>
        }
      >
        <p>Вы перестанете получать новости и предложения AIESEC.</p>
      </Dialog>
    </section>
  );
}
