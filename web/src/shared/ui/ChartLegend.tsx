export interface LegendEntry { id: string; label: string; colour: string }

export function ChartLegend({ entries }: { entries: LegendEntry[] }) {
  return (
    <ul className="ui-chart-legend">
      {entries.map((e) => (
        <li key={e.id}><span style={{ background: e.colour }} aria-hidden />{e.label}</li>
      ))}
    </ul>
  );
}