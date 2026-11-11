import type { FormOption } from "../api/types";

export interface SegmentedProps {
  options: FormOption[];
  value: string | null;
  onChange: (v: string) => void;
}

export function Segmented({ options, value, onChange }: SegmentedProps) {
  return (
    <div role="radiogroup" className="ui-segmented">
      {options.map((o) => (
        <button
          key={o.code}
          type="button"
          role="radio"
          aria-checked={value === o.code}
          disabled={o.disabled}
          className={value === o.code ? "ui-segmented__item ui-segmented__item--on" : "ui-segmented__item"}
          onClick={() => onChange(o.code)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}