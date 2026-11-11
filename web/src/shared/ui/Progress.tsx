export interface ProgressProps {
  value: number;
  max?: number;
  label?: string;
}

export function Progress({ value, max = 1, label }: ProgressProps) {
  const pct = Math.max(0, Math.min(1, value / max)) * 100;
  return (
    <div className="ui-progress">
      <div className="ui-progress__bar"><div className="ui-progress__fill" style={{ width: `${pct}%` }} /></div>
      {label && <div className="ui-progress__label">{label}</div>}
    </div>
  );
}