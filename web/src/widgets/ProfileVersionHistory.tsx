import { useQuery } from "@tanstack/react-query";
import { api } from "../shared/api/endpoints";
import { qk } from "../shared/api/queries";
import { formatDateTime } from "../shared/lib/date";
import { Skeleton } from "../shared/ui/Skeleton";
import { ErrorBanner } from "../shared/ui/ErrorBanner";
import { EmptyState } from "../shared/ui/EmptyState";

export function ProfileVersionHistory() {
  const q = useQuery({ queryKey: qk.profileVersions, queryFn: () => api.listProfileVersions() });
  if (q.isLoading) return <Skeleton lines={3} />;
  if (q.error) return <ErrorBanner error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data || q.data.length === 0) return <EmptyState title="Версий пока нет" />;
  return (
    <ol className="stack" style={{ listStyle: "none", padding: 0 }}>
      {q.data.map((v) => (
        <li key={v.version} className="ui-card">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <strong>Версия {v.version}</strong>
            <span className="muted">{formatDateTime(v.created_at)}</span>
          </div>
          <div className="muted">Заполненность: {Math.round(v.completeness * 100)}%</div>
        </li>
      ))}
    </ol>
  );
}