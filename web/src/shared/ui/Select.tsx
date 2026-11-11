import type { FormOption } from "../api/types";

export interface SelectProps {
  options: FormOption[];
  value: string | null;
  onChange: (v: string | null) => void;
  placeholder?: string;
  allowCustom?: boolean;
}

export function Select({ options, value, onChange, placeholder = "Выберите", allowCustom = false }: SelectProps) {
  const isCustom = allowCustom && value !== null && !options.some((o) => o.code === value);
  return (
    <div className="ui-select">
      <select value={isCustom ? "__custom__" : value ?? ""} onChange={(e) => {
        const v = e.target.value;
        onChange(v === "" ? null : v === "__custom__" ? "" : v);
      }}>
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o.code} value={o.code} disabled={o.disabled}>{o.label}</option>
        ))}
        {allowCustom && <option value="__custom__">Другое</option>}
      </select>
      {allowCustom && isCustom && (
        <input
          type="text"
          value={value ?? ""}
          placeholder="Введите своё значение"
          onChange={(e) => onChange(e.target.value || null)}
        />
      )}
    </div>
  );
}