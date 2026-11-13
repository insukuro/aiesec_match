import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { fetchers, qk } from "../../shared/api/queries";
import { SubscriptionForm } from "../../features/subscription/SubscriptionForm";
import { LinkTelegramPanel } from "../../features/account/LinkTelegramPanel";
import { DeleteAccountDialog } from "../../features/account/DeleteAccountDialog";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useAuth } from "../../features/auth/AuthContext";
import { GuestBanner } from "../../widgets/GuestBanner";
import { EmptyState } from "../../shared/ui/EmptyState";

export function SettingsPage() {
  const nav = useNavigate();
  const qc = useQueryClient();
  const { isGuest, me, logout } = useAuth();
  const [confirmDelete, setConfirmDelete] = useState(false);
  useEffect(() => { document.title = "Настройки — AIESEC Match"; }, []);

  const subQ = useQuery({ queryKey: qk.subscription, queryFn: fetchers.subscription, enabled: !isGuest });
  const deleteMe = useMutation({
    mutationFn: () => api.deleteMe(),
    onSuccess: () => {
      localStorage.removeItem("device_secret");
      logout();
      qc.clear();
      nav(ROUTES.welcome);
    },
  });

  if (isGuest) {
    return (
      <main className="page">
        <h1 className="page__title">Настройки</h1>
        <GuestBanner />
        <EmptyState
          title="Создайте аккаунт"
          description="Уведомления, привязка Telegram и удаление данных доступны только в аккаунте."
          action={<Button onClick={() => nav(ROUTES.register)}>Создать аккаунт</Button>}
        />
      </main>
    );
  }

  if (subQ.isLoading) return <main className="page"><Skeleton lines={4} /></main>;
  if (subQ.error) return <main className="page"><ErrorBanner error={subQ.error} onRetry={() => subQ.refetch()} /></main>;

  return (
    <main className="page">
      <h1 className="page__title">Настройки</h1>

      {me?.email && (
        <section className="section">
          <h2 className="section__title">Аккаунт</h2>
          <div className="ui-card">
            <div className="row" style={{ justifyContent: "space-between" }}>
              <span className="muted">Email</span>
              <strong>{me.email}</strong>
            </div>
            <div className="row" style={{ marginTop: "var(--space-3)" }}>
              <Button variant="outline" onClick={() => { logout(); nav(ROUTES.welcome); }}>Выйти</Button>
            </div>
          </div>
        </section>
      )}

      <section className="section">
        <h2 className="section__title">Уведомления</h2>
        {subQ.data && <SubscriptionForm initial={subQ.data} />}
      </section>

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