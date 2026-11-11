import { PROGRAMME_COLORS } from "../config/brand";
import type { ProgrammeKind } from "../api/types";

export interface DonutSlice {
  id: string;
  label: string;
  value: number;
  color?: string;
  programme?: ProgrammeKind;
}

export interface DonutChartProps {
  slices: DonutSlice[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  onSliceClick?: (id: string) => void;
}

export function DonutChart({
  slices,
  size = 180,
  thickness = 24,
  centerLabel,
  onSliceClick,
}: DonutChartProps) {
  const total = slices.reduce((acc, s) => acc + s.value, 0);
  const radius = (size - thickness) / 2;
  const circ = 2 * Math.PI * radius;
  let offset = 0;
  const colorOf = (s: DonutSlice) =>
    s.color ?? (s.programme ? PROGRAMME_COLORS[s.programme] : "#037EF3");
  return (
    <div className="ui-donut">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Диаграмма">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#EEEFF3" strokeWidth={thickness} />
        {total === 0 ? null : slices.map((s) => {
          const fraction = s.value / total;
          const dash = fraction * circ;
          const el = (
            <circle
              key={s.id}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={colorOf(s)}
              strokeWidth={thickness}
              strokeDasharray={`${dash} ${circ - dash}`}
              strokeDashoffset={-offset}
              transform={`rotate(-90 ${size / 2} ${size / 2})`}
              onClick={() => onSliceClick?.(s.id)}
              style={{ cursor: onSliceClick ? "pointer" : "default" }}
            >
              <title>{`${s.label}: ${s.value}`}</title>
            </circle>
          );
          offset += dash;
          return el;
        })}
        {centerLabel && (
          <text x="50%" y="50%" textAnchor="middle" dominantBaseline="central" fontSize={size * 0.16}>
            {centerLabel}
          </text>
        )}
      </svg>
      <ul className="ui-donut__legend">
        {slices.map((s) => (
          <li key={s.id}>
            <span className="ui-donut__dot" style={{ background: colorOf(s) }} aria-hidden />
            <span>{s.label}</span>
            <span className="ui-donut__value">{s.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}