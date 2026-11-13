import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import { HistoryEventItem } from "../../entities/history/HistoryEventItem";
import { DateRangeFilter, type Period } from "../../shared/ui/DateRangeFilter";
import { EmptyState } from "../../shared/ui/EmptyState";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Skeleton } from "../../shared/ui/Skeleton";
import { Button } from "../../shared/ui/Button";
import { Chip } from "../../shared/ui/Chip";
import type { HistoryType } from "../../shared/api/types";
import { useAuth } from "../../features/auth/AuthContext";
import { GuestBanner } from "../../widgets/GuestBanner";
import { ROUTES } from "../../app/routes";

const TYPES: Array<{ id: HistoryType | "all"; label: string }> = [
  { id: "all", label: "Все события" },
  { id: "profile_updated", label: "Профиль" },
  { id: "run_finished", label: "Подбор" },
  { id: "signal_liked", label: "Отметки" },
  { id: "signal_applied", label: "Отклики" },
  { id: "opportunity_viewed", label: "Просмотры" },
];

export function HistoryPage() {
  const nav = useNavigate();
  const { isGuest } = useAuth();
  const [type, setType] = useState<HistoryType | "all">("all");
  const [period, setPeriod] = useState<Period>("30d");
  const [from, setFrom] = useState<string | undefined>();
  const [to, setTo] = useState<string | undefined>();
  const [offset, setOffset] = useState(0);
  const limit = 20;

  useEffect(() => { document.title = "История — AIESEC Match"; }, []);

  const params = { type: type === "all" ? undefined : type, from, to, limit, offset };
  const q = useQuery({
    queryKey: qk.history(params as Record<string, unknown>),
    queryFn: () => api.getHistory(params as Record<string, string | number | undefined>),
    enabled: !isGuest,
  });

  if (isGuest) {
    return (
      <main className="page">
        <h1 className="page__title">История</h1>
        <GuestBanner />
        <EmptyState
          title="Создайте аккаунт"
          description="История доступна только в аккаунте."
          action={<Button onClick={() => nav(ROUTES.register)}>Создать аккаунт</Button>}
        />
      </main>
    );
  }

  return (
    <main className="page">
      <h1 className="page__title">История</h1>

      <div className="row" style={{ marginBottom: "var(--space-3)" }}>
        {TYPES.map((t) => (
          <Chip key={t.id} selected={type === t.id} onClick={() => { setType(t.id); setOffset(0); }}>
            {t.label}
          </Chip>
        ))}
      </div>

      <DateRangeFilter
        period={period}
        from={from}
        to={to}
        onChange={(p, f, t) => { setPeriod(p); setFrom(f); setTo(t); setOffset(0); }}
      />

      {q.isLoading && <Skeleton lines={6} />}
      {q.error && <ErrorBanner error={q.error} onRetry={() => q.refetch()} />}
      {q.data && q.data.items.length === 0 && (
        <EmptyState title="Пока нет событий" description="Как только вы начнёте пользоваться сервисом, здесь появится активность" />
      )}
      {q.data && q.data.items.length > 0 && (
        <ul className="stack" style={{ listStyle: "none", padding: 0 }}>
          {q.data.items.map((e) => <HistoryEventItem key={e.event_id} event={e} />)}
        </ul>
      )}
      {q.data && q.data.total > limit && (
        <div className="row" style={{ justifyContent: "center", marginTop: "var(--space-4)" }}>
          <Button variant="outline" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - limit))}>Назад</Button>
          <span className="muted">{offset + 1}–{Math.min(offset + limit, q.data.total)} из {q.data.total}</span>
          <Button variant="outline" disabled={offset + limit >= q.data.total} onClick={() => setOffset(offset + limit)}>Далее</Button>
        </div>
      )}
    </main>
  );
}