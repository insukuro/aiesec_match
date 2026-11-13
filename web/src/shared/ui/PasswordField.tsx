import { useState } from "react";

export interface PasswordFieldProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  minLength?: number;
}

export function PasswordField({ value, onChange, placeholder, autoComplete = "current-password", minLength }: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="ui-password">
      <input
        className="ui-input"
        type={visible ? "text" : "password"}
        value={value}
        placeholder={placeholder}
        autoComplete={autoComplete}
        minLength={minLength}
        onChange={(e) => onChange(e.target.value)}
      />
      <button
        type="button"
        className="ui-password__toggle"
        aria-label={visible ? "Скрыть пароль" : "Показать пароль"}
        onClick={() => setVisible((v) => !v)}
      >
        {visible ? "🙈" : "👁"}
      </button>
    </div>
  );
}