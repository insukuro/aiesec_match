import { useCallback, useMemo, useState } from "react";
import type { FormStep } from "../../shared/api/types";
import { evaluate } from "../../shared/lib/condition";
import { getPath, setPath, stripEmpty } from "../../shared/lib/get";

export function useFormState(step: FormStep, initial: Record<string, unknown>) {
  const [values, setValues] = useState<Record<string, unknown>>(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const visibleFields = useMemo(
    () => step.fields.filter((f) => evaluate(f.show_if, values)),
    [step.fields, values]
  );

  const update = useCallback((fieldId: string, mapsTo: string | undefined, value: unknown) => {
    setValues((prev) => setPath(prev, mapsTo ?? fieldId, value));
    setErrors((prev) => ({ ...prev, [fieldId]: "" }));
  }, []);

  const validate = useCallback((): boolean => {
    const next: Record<string, string> = {};
    for (const f of visibleFields) {
      const v = getPath(values, f.maps_to ?? f.id);
      const empty = v == null || v === "" || (Array.isArray(v) && v.length === 0);
      if (f.required && empty) next[f.id] = "Обязательное поле";
      const max = f.validation?.max_length;
      if (max && typeof v === "string" && v.length > max) next[f.id] = `Не более ${max} символов`;
      const num = f.validation;
      if (num?.min != null && typeof v === "number" && v < num.min) next[f.id] = `Минимум ${num.min}`;
      if (num?.max != null && typeof v === "number" && v > num.max) next[f.id] = `Максимум ${num.max}`;
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }, [visibleFields, values]);

  const sanitized = useMemo(() => stripEmpty(values), [values]);

  return { values, errors, visibleFields, update, validate, sanitized };
}