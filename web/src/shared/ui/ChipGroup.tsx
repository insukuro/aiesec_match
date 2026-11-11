import type { FormOption } from "../api/types";
import { Chip } from "./Chip";

export interface ChipGroupProps {
  options: FormOption[];
  value: string[];
  multi?: boolean;
  onChange: (next: string[]) => void;
}

export function ChipGroup({ options, value, multi = true, onChange }: ChipGroupProps) {
  const toggle = (code: string) => {
    if (multi) {
      onChange(value.includes(code) ? value.filter((v) => v !== code) : [...value, code]);
    } else {
      onChange([code]);
    }
  };
  return (
    <div className="ui-chip-group" role="group">
      {options.map((o) => (
        <Chip
          key={o.code}
          role={multi ? "checkbox" : "radio"}
          aria-checked={value.includes(o.code)}
          selected={value.includes(o.code)}
          disabled={o.disabled}
          onClick={() => toggle(o.code)}
          title={o.description}
        >
          {o.label}
          {typeof o.count === "number" && <span className="ui-chip__count">{o.count}</span>}
        </Chip>
      ))}
    </div>
  );
}