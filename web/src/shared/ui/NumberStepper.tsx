export interface NumberStepperProps {
  value: number | undefined;
  min: number;
  max: number;
  onChange: (v: number) => void;
}

export function NumberStepper({ value, min, max, onChange }: NumberStepperProps) {
  const v = value ?? min;
  return (
    <div className="ui-stepper">
      <button type="button" aria-label="Уменьшить" onClick={() => onChange(Math.max(min, v - 1))} disabled={v <= min}>−</button>
      <span aria-live="polite">{v}</span>
      <button type="button" aria-label="Увеличить" onClick={() => onChange(Math.min(max, v + 1))} disabled={v >= max}>+</button>
    </div>
  );
}