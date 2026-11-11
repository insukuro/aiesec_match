export interface DateFieldProps {
  value: string | null;
  onChange: (v: string | null) => void;
  min?: string;
  max?: string;
}

export function DateField({ value, onChange, min, max }: DateFieldProps) {
  return (
    <input
      type="date"
      className="ui-input"
      value={value ?? ""}
      min={min}
      max={max}
      onChange={(e) => onChange(e.target.value || null)}
    />
  );
}