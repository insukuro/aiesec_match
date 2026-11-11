export interface LinePoint { x: string; y: number }

export interface LineSeries {
  id: string;
  label: string;
  colour: string;
  points: LinePoint[];
}

export function LineChart({ series, height = 180, ariaLabel }: { series: LineSeries[]; height?: number; ariaLabel: string }) {
  const all = series.flatMap((s) => s.points);
  const maxY = Math.max(1, ...all.map((p) => p.y));
  const width = 600;
  const padding = 24;
  const drawPath = (points: LinePoint[]) => {
    if (points.length === 0) return "";
    const stepX = (width - padding * 2) / Math.max(1, points.length - 1);
    return points
      .map((p, i) => {
        const x = padding + i * stepX;
        const y = height - padding - (p.y / maxY) * (height - padding * 2);
        return `${i === 0 ? "M" : "L"}${x},${y}`;
      })
      .join(" ");
  };
  return (
    <div className="ui-line" role="img" aria-label={ariaLabel}>
      <svg width="100%" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="xMidYMid meet">
        {series.map((s) => (
          <path key={s.id} d={drawPath(s.points)} fill="none" stroke={s.colour} strokeWidth={2} />
        ))}
      </svg>
      <ul className="ui-line__legend">
        {series.map((s) => (
          <li key={s.id}><span style={{ background: s.colour }} />{s.label}</li>
        ))}
      </ul>
    </div>
  );
}