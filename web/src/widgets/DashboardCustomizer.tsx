import { useEffect, useState } from "react";
import { useDashboardPreferences } from "../features/dashboard/useDashboardPreferences";
import { Toggle } from "../shared/ui/Toggle";
import { Button } from "../shared/ui/Button";
import { CHART_IDS, type ChartId } from "../shared/api/types";
import { Skeleton } from "../shared/ui/Skeleton";

const LABELS: Record<ChartId, string> = {
  profile_completeness: "Заполненность профиля",
  programme_distribution: "Распределение по программам",
  interests_distribution: "Интересы",
  activity_series: "Активность",
  recommendation_statistics: "Рекомендации",
};

export function DashboardCustomizer() {
  const { data, save, reset, isSaving } = useDashboardPreferences();
  const [visible, setVisible] = useState<string[]>([]);
  const [order, setOrder] = useState<string[]>([]);

  useEffect(() => {
    if (data) {
      setVisible(data.visible_charts);
      setOrder(data.order);
    }
  }, [data]);

  if (!data) return <Skeleton lines={4} />;

  const toggle = (id: ChartId) => {
    setVisible((v) => (v.includes(id) ? v.filter((x) => x !== id) : [...v, id]));
  };
  const move = (id: ChartId, dir: -1 | 1) => {
    const idx = order.indexOf(id);
    if (idx < 0) return;
    const next = [...order];
    const target = idx + dir;
    if (target < 0 || target >= next.length) return;
    [next[idx], next[target]] = [next[target]!, next[idx]!];
    setOrder(next);
  };

  return (
    <div className="stack">
      <section className="ui-card">
        <h3>Какие диаграммы показывать</h3>
        <div className="stack">
          {CHART_IDS.map((id) => (
            <Toggle
              key={id}
              label={LABELS[id]}
              value={visible.includes(id)}
              onChange={() => toggle(id)}
            />
          ))}
        </div>
      </section>

      <section className="ui-card">
        <h3>Порядок</h3>
        <ol className="stack" style={{ paddingLeft: 0, listStyle: "none" }}>
          {order.map((id, i) => (
            <li key={id} className="row" style={{ justifyContent: "space-between" }}>
              <span>{LABELS[id as ChartId]}</span>
              <span className="row">
                <Button variant="text" onClick={() => move(id as ChartId, -1)} disabled={i === 0}>↑</Button>
                <Button variant="text" onClick={() => move(id as ChartId, 1)} disabled={i === order.length - 1}>↓</Button>
              </span>
            </li>
          ))}
        </ol>
      </section>

      <div className="row">
        <Button onClick={() => save({ ...data, visible_charts: visible, order })} disabled={isSaving}>Сохранить</Button>
        <Button variant="outline" onClick={() => reset()} disabled={isSaving}>По умолчанию</Button>
      </div>
    </div>
  );
}