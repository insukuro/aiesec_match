export interface ChartTooltipProps {
  label: string;
  value: string;
  visible: boolean;
  x: number;
  y: number;
}

export function ChartTooltip({ label, value, visible, x, y }: ChartTooltipProps) {
  if (!visible) return null;
  return (
    <div className="ui-chart-tooltip" style={{ left: x, top: y }} role="status">
      <strong>{label}</strong>
      <span>{value}</span>
    </div>
  );
}