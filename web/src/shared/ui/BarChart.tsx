import { PROGRAMME_COLORS } from "../config/brand";
import type { ProgrammeKind } from "../api/types";

export interface BarDatum {
  id: string;
  label: string;
  value: number;
  colour?: string;
  programme?: ProgrammeKind;
}

export function BarChart({ data, height = 160, horizontal = false, ariaLabel }: { data: BarDatum[]; height?: number; horizontal?: boolean; ariaLabel: string }) {
  const max = Math.max(1, ...data.map((d) => d.value));
  const colorOf = (d: BarDatum) => d.colour ?? (d.programme ? PROGRAMME_COLORS[d.programme] : "#037EF3");
  if (horizontal) {
    return (
      <ul className="ui-bar ui-bar--h" aria-label={ariaLabel}>
        {data.map((d) => (
          <li key={d.id}>
            <span className="ui-bar__label">{d.label}</span>
            <span className="ui-bar__track">
              <span className="ui-bar__fill" style={{ width: `${(d.value / max) * 100}%`, background: colorOf(d) }} />
            </span>
            <span className="ui-bar__value">{d.value}</span>
          </li>
        ))}
      </ul>
    );
  }
  return (
    <div className="ui-bar ui-bar--v" style={{ height }} aria-label={ariaLabel}>
      {data.map((d) => (
        <div key={d.id} className="ui-bar__col">
          <div className="ui-bar__fill" style={{ height: `${(d.value / max) * 100}%`, background: colorOf(d) }} />
          <span className="ui-bar__label">{d.label}</span>
        </div>
      ))}
    </div>
  );
}