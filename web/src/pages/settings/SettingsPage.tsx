import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { SubscriptionForm } from "../../features/subscription/SubscriptionForm";
import { LinkTelegramPanel } from "../../features/account/LinkTelegramPanel";
import { DeleteAccountDialog } from "../../features/account/DeleteAccountDialog";
import { AccountSecurityForm } from "../../features/account/AccountSecurityForm";
import { ConsentSettings } from "../../features/consent/ConsentSettings";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useAuth } from "../../features/auth/AuthContext";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";

export function SettingsPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const { me, logout, refreshMe } = useAuth();
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => { document.title = "Настройки — AIESEC Match"; }, []);

  const subQ = useQuery({ queryKey: qk.subscription, queryFn: fetchers.subscription });
  const deleteMe = useMutation({
    mutationFn: () => api.deleteMe(),
    onSuccess: () => {
      logout();
      qc.clear();
      nav(ROUTES.welcome);
    },
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  return (
    <main className="page">
      <h1 className="page__title">Настройки</h1>

      {me?.email && (
        <section className="section">
          <h2 className="section__title">Аккаунт и безопасность</h2>
          <AccountSecurityForm
            email={me.email}
            emailVerified={me.email_verified}
            refreshMe={refreshMe}
          />
          <div className="ui-card section">
            <div className="row" style={{ marginTop: "var(--space-3)" }}>
              <Button variant="outline" onClick={() => { logout(); nav(ROUTES.welcome); }}>Выйти</Button>
            </div>
          </div>
        </section>
      )}

      <section className="section">
        <h2 className="section__title">Настройки уведомлений</h2>
        {subQ.isLoading && <Skeleton lines={3} />}
        {subQ.error && <ErrorBanner error={subQ.error} onRetry={() => subQ.refetch()} />}
        {subQ.data && <SubscriptionForm initial={subQ.data} />}
      </section>

      <ConsentSettings acceptedConsents={me?.consents ?? []} refreshMe={refreshMe} />

      <section className="section">
        <h2 className="section__title">Привязка Telegram</h2>
        <LinkTelegramPanel />
      </section>

      <section className="section">
        <h2 className="section__title">Удаление данных</h2>
        <p className="muted">Аккаунт и все данные будут удалены безвозвратно.</p>
        <Button variant="danger" onClick={() => setConfirmDelete(true)}>Удалить аккаунт</Button>
      </section>

      <DeleteAccountDialog
        open={confirmDelete}
        busy={deleteMe.isPending}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => deleteMe.mutate()}
      />
    </main>
  );
}