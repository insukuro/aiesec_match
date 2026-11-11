import { isoDate, daysAgo } from "../lib/date";

export type Period = "7d" | "30d" | "90d" | "all" | "custom";

export interface DateRangeFilterProps {
  period: Period;
  from?: string;
  to?: string;
  onChange: (period: Period, from?: string, to?: string) => void;
}

export function DateRangeFilter({ period, from, to, onChange }: DateRangeFilterProps) {
  const setPreset = (p: Exclude<Period, "custom">) => {
    if (p === "all") return onChange("all");
    const days = p === "7d" ? 7 : p === "30d" ? 30 : 90;
    onChange(p, isoDate(daysAgo(days)), isoDate(new Date()));
  };
  return (
    <div className="ui-daterange">
      {(["7d", "30d", "90d", "all"] as const).map((p) => (
        <button
          key={p}
          type="button"
          className={period === p ? "ui-daterange__btn ui-daterange__btn--on" : "ui-daterange__btn"}
          onClick={() => setPreset(p)}
        >
          {p === "7d" ? "7 дней" : p === "30d" ? "30 дней" : p === "90d" ? "90 дней" : "Всё время"}
        </button>
      ))}
      <div className="ui-daterange__custom">
        <input type="date" value={from ?? ""} onChange={(e) => onChange("custom", e.target.value, to)} />
        <span>—</span>
        <input type="date" value={to ?? ""} onChange={(e) => onChange("custom", from, e.target.value)} />
      </div>
    </div>
  );
}