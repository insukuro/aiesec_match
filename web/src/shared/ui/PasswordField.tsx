import { useMemo, useState } from "react";
import { checkPassword, passwordStrengthLabel } from "../lib/password";

export interface PasswordFieldProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  minLength?: number;
  email?: string;
  showStrength?: boolean;
  error?: string;
}

export function PasswordField({
  value,
  onChange,
  placeholder,
  autoComplete = "current-password",
  minLength,
  email,
  showStrength = false,
  error,
}: PasswordFieldProps) {
  const [visible, setVisible] = useState(false);
  const check = useMemo(() => checkPassword(value, email), [value, email]);

  return (
    <div className="ui-password">
      <div className="ui-password__row">
        <input
          className={`ui-input ${error ? "ui-input--error" : ""}`}
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
      {showStrength && value.length > 0 && (
        <div className="ui-password__strength">
          <div className="ui-password__bars">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className={
                  "ui-password__bar" +
                  (check.score > i ? " ui-password__bar--on" : "")
                }
              />
            ))}
          </div>
          <span className="ui-password__label">{passwordStrengthLabel(check.score)}</span>
        </div>
      )}
      {error && <span className="field__error">{error}</span>}
      {!error && showStrength && value.length > 0 && check.errors.length > 0 && (
        <span className="field__hint">{check.errors[0]}</span>
      )}
    </div>
  );
}