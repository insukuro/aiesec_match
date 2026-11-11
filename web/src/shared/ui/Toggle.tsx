export interface ToggleProps {
  value: boolean;
  onChange: (v: boolean) => void;
  label?: string;
  disabled?: boolean;
}

export function Toggle({ value, onChange, label, disabled = false }: ToggleProps) {
  return (
    <label className="ui-toggle">
      <button
        type="button"
        role="switch"
        aria-checked={value}
        disabled={disabled}
        className={value ? "ui-toggle__track ui-toggle__track--on" : "ui-toggle__track"}
        onClick={() => onChange(!value)}
      >
        <span className="ui-toggle__thumb" />
      </button>
      {label && <span className="ui-toggle__label">{label}</span>}
    </label>
  );
}