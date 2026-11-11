import { useQuery } from "@tanstack/react-query";
import { api } from "../shared/api/endpoints";
import { qk } from "../shared/api/queries";
import { useDashboardPreferences } from "../features/dashboard/useDashboardPreferences";
import { DonutChart } from "../shared/ui/DonutChart";
import { BarChart } from "../shared/ui/BarChart";
import { LineChart } from "../shared/ui/LineChart";
import { ErrorBanner } from "../shared/ui/ErrorBanner";
import { Skeleton } from "../shared/ui/Skeleton";
import { EmptyState } from "../shared/ui/EmptyState";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../shared/config/brand";
import type { ChartId } from "../shared/api/types";

export function UserStatisticsDashboard() {
  const prefs = useDashboardPreferences();
  const period = prefs.data?.period ?? "30d";
  const q = useQuery({
    queryKey: qk.analytics(period),
    queryFn: () => api.getAnalytics(period),
    retry: 1,
  });

  if (prefs.isLoading) return <Skeleton lines={4} />;
  if (q.isLoading) return <Skeleton lines={6} />;
  if (q.error) return <ErrorBanner error={q.error} onRetry={() => q.refetch()} />;
  if (!q.data) return null;

  const visible = prefs.data?.visible_charts ?? [];
  const order = prefs.data?.order ?? visible;

  const renderers: Record<ChartId, () => JSX.Element> = {
    profile_completeness: () => (
      <section className="ui-card">
        <h3>Заполненность профиля</h3>
        <DonutChart
          slices={[
            { id: "filled", label: "Заполнено", value: q.data!.profile_completeness.filled, color: "#037EF3" },
            { id: "empty", label: "Осталось", value: Math.max(0, q.data!.profile_completeness.total - q.data!.profile_completeness.filled), color: "#E6E8EE" },
          ]}
          centerLabel={`${q.data!.profile_completeness.percent}%`}
        />
      </section>
    ),
    programme_distribution: () =>
      q.data!.programme_distribution.length === 0 ? (
        <EmptyState title="Программы не выбраны" />
      ) : (
        <section className="ui-card">
          <h3>Распределение по программам</h3>
          <DonutChart
            slices={q.data!.programme_distribution.map((p) => ({
              id: p.programme_kind,
              label: PROGRAMME_LABEL[p.programme_kind],
              value: p.count,
              programme: p.programme_kind,
            }))}
          />
        </section>
      ),
    interests_distribution: () =>
      q.data!.interests_distribution.length === 0 ? (
        <EmptyState title="Интересы не указаны" />
      ) : (
        <section className="ui-card">
          <h3>Интересы</h3>
          <BarChart
            horizontal
            ariaLabel="Распределение интересов"
            data={q.data!.interests_distribution.map((i) => ({
              id: i.code,
              label: i.label,
              value: i.count,
              colour: "#037EF3",
            }))}
          />
        </section>
      ),
    activity_series: () =>
      q.data!.activity_series.length === 0 ? (
        <EmptyState title="Пока нет активности" />
      ) : (
        <section className="ui-card">
          <h3>Активность</h3>
          <LineChart
            ariaLabel="Активность по дням"
            series={[
              { id: "run_started", label: "Подбор", colour: PROGRAMME_COLORS.talent, points: q.data!.activity_series.map((p) => ({ x: p.bucket, y: p.run_started })) },
              { id: "viewed", label: "Просмотры", colour: "#037EF3", points: q.data!.activity_series.map((p) => ({ x: p.bucket, y: p.viewed })) },
              { id: "liked", label: "Отметки", colour: PROGRAMME_COLORS.teacher, points: q.data!.activity_series.map((p) => ({ x: p.bucket, y: p.liked })) },
              { id: "applied", label: "Отклики", colour: PROGRAMME_COLORS.volunteer, points: q.data!.activity_series.map((p) => ({ x: p.bucket, y: p.applied })) },
            ]}
          />
        </section>
      ),
    recommendation_statistics: () =>
      q.data!.recommendation_statistics.length === 0 ? (
        <EmptyState title="Рекомендаций пока нет" />
      ) : (
        <section className="ui-card">
          <h3>Рекомендации по программам</h3>
          <BarChart
            ariaLabel="Рекомендации по программам"
            data={q.data!.recommendation_statistics.map((r) => ({
              id: r.programme_kind,
              label: PROGRAMME_LABEL[r.programme_kind],
              value: r.count,
              programme: r.programme_kind,
            }))}
          />
        </section>
      ),
  };

  return (
    <div className="stack">
      {order.filter((id): id is ChartId => (visible as string[]).includes(id)).map((id) => (
        <div key={id}>{renderers[id]()}</div>
      ))}
    </div>
  );
}