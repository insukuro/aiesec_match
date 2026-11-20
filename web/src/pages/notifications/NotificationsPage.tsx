import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import { formatDateTime } from "../../shared/lib/date";
import { Button } from "../../shared/ui/Button";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { useToast } from "../../shared/ui/Toast";
import { errorMessage } from "../../shared/lib/errors";

const LIMIT = 20;

export function NotificationsPage() {
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [offset, setOffset] = useState(0);
  const notifications = useQuery({
    queryKey: qk.notifications({ limit: LIMIT, offset }),
    queryFn: () => api.getNotifications({ limit: LIMIT, offset }),
  });
  const markRead = useMutation({
    mutationFn: (id: string) => api.markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: qk.notificationsRoot }),
    onError: (error) => toast.show(errorMessage(error), "error"),
  });

  useEffect(() => { document.title = "Уведомления — AIESEC Match"; }, []);

  return (
    <main className="page">
      <h1 className="page__title">Уведомления</h1>
      {notifications.data && (
        <p className="muted" aria-live="polite">
          Непрочитанных: {notifications.data.unread}
        </p>
      )}
      {notifications.isLoading && <Skeleton lines={5} />}
      {notifications.error && (
        <ErrorBanner error={notifications.error} onRetry={() => notifications.refetch()} />
      )}
      {notifications.data?.items.length === 0 && (
        <EmptyState title="Пока нет уведомлений" description="Новые совпадения появятся здесь." />
      )}
      {notifications.data && notifications.data.items.length > 0 && (
        <>
          <ul className="stack" style={{ listStyle: "none", padding: 0 }}>
            {notifications.data.items.map((item) => {
              const runId = item.payload.run_id;
              return (
                <li className="ui-card" key={item.notification_id}>
                  <div className="row" style={{ justifyContent: "space-between" }}>
                    <strong>{item.kind === "new_matches" ? "Новые совпадения" : "Уведомление"}</strong>
                    <time className="muted" dateTime={item.created_at}>
                      {formatDateTime(item.created_at)}
                    </time>
                  </div>
                  {typeof runId === "string" && (
                    <div className="row section">
                      <Button variant="outline" onClick={() => nav(`/results?run=${encodeURIComponent(runId)}`)}>
                        Посмотреть подбор
                      </Button>
                    </div>
                  )}
                  {!item.read_at && (
                    <div className="row section">
                      <Button
                        variant="text"
                        disabled={markRead.isPending}
                        onClick={() => markRead.mutate(item.notification_id)}
                      >
                        Отметить прочитанным
                      </Button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
          {notifications.data.total > LIMIT && (
            <div className="row" style={{ justifyContent: "center", marginTop: "var(--space-4)" }}>
              <Button
                variant="outline"
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - LIMIT))}
              >
                Назад
              </Button>
              <span className="muted">
                {offset + 1}–{Math.min(offset + LIMIT, notifications.data.total)} из {notifications.data.total}
              </span>
              <Button
                variant="outline"
                disabled={offset + LIMIT >= notifications.data.total}
                onClick={() => setOffset(offset + LIMIT)}
              >
                Далее
              </Button>
            </div>
          )}
        </>
      )}
    </main>
  );
}
