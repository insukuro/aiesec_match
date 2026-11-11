import { useState } from "react";
import type { FormOptions, FormStep } from "../../shared/api/types";
import { getPath } from "../../shared/lib/get";
import { useFormState } from "./useFormState";
import { FieldRenderer } from "./FieldRenderer";
import { Button } from "../../shared/ui/Button";

export interface FormRendererProps {
  step: FormStep;
  options: FormOptions;
  initialValues: Record<string, unknown>;
  onNext: (values: Record<string, unknown>) => Promise<void> | void;
  onBack?: () => void;
  onDirty?: () => void;
}

export function FormRenderer({ step, options, initialValues, onNext, onBack, onDirty }: FormRendererProps) {
  const { values, errors, visibleFields, update, validate, sanitized } = useFormState(step, initialValues);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    if (!validate()) return;
    setBusy(true);
    try {
      await onNext(sanitized);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form
      className="stack"
      onSubmit={(e) => { e.preventDefault(); void submit(); }}
      onChange={() => onDirty?.()}
    >
      <h2 className="form__step-title">{step.title}</h2>
      {step.description && <p className="muted">{step.description}</p>}

      {visibleFields.map((f) => (
        <div className="field" key={f.id}>
          <label className="field__label" htmlFor={f.id}>
            {f.label}
            {f.required && <span aria-hidden> *</span>}
          </label>
          <FieldRenderer
            id={f.id}
            field={f}
            value={getPath(values, f.maps_to ?? f.id)}
            options={f.options_source ? options[f.options_source] ?? [] : f.options ?? []}
            onChange={(v) => update(f.id, f.maps_to, v)}
          />
          {f.help && <span className="field__hint">{f.help}</span>}
          {errors[f.id] && <span className="field__error">{errors[f.id]}</span>}
        </div>
      ))}

      <div className="form__actions">
        {onBack ? <Button variant="outline" onClick={onBack} disabled={busy}>Назад</Button> : <span />}
        <Button type="submit" disabled={busy}>{busy ? "Сохраняем…" : "Далее"}</Button>
      </div>
    </form>
  );
}