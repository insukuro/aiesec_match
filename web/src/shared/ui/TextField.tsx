import type { InputHTMLAttributes } from "react";

export interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "onChange"> {
  value: string | null;
  onChange: (v: string) => void;
}

export function TextField({ value, onChange, className = "", ...rest }: TextFieldProps) {
  return (
    <input
      className={`ui-input ${className}`}
      value={value ?? ""}
      onChange={(e) => onChange(e.target.value)}
      {...rest}
    />
  );
}