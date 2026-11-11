import type { FormField, FormOption } from "../../shared/api/types";
import { ChipGroup } from "../../shared/ui/ChipGroup";
import { Segmented } from "../../shared/ui/Segmented";
import { Select } from "../../shared/ui/Select";
import { Toggle } from "../../shared/ui/Toggle";
import { NumberStepper } from "../../shared/ui/NumberStepper";
import { DateField } from "../../shared/ui/DateField";
import { TextArea } from "../../shared/ui/TextArea";
import { TextField } from "../../shared/ui/TextField";

export interface FieldRendererProps {
  id: string;
  field: FormField;
  value: unknown;
  options: FormOption[];
  onChange: (v: unknown) => void;
}

export function FieldRenderer({ id, field, value, options, onChange }: FieldRendererProps) {
  const widget = field.ui?.widget;

  switch (field.kind) {
    case "boolean":
      return <Toggle value={Boolean(value)} onChange={onChange} />;

    case "date":
      return (
        <DateField
          value={value ? String(value) : null}
          onChange={(v) => onChange(v)}
          max={new Date().toISOString().slice(0, 10)}
        />
      );

    case "number":
      return widget === "stepper" ? (
        <NumberStepper
          value={typeof value === "number" ? value : undefined}
          min={field.validation?.min ?? 0}
          max={field.validation?.max ?? 100}
          onChange={onChange}
        />
      ) : (
        <TextField
          id={id}
          type="number"
          value={value == null ? null : String(value)}
          onChange={(v) => onChange(v === "" ? null : Number(v))}
          min={field.validation?.min}
          max={field.validation?.max}
        />
      );

    case "text":
      return <TextField id={id} value={value == null ? null : String(value)} onChange={onChange} maxLength={field.validation?.max_length} />;

    case "textarea":
      return <TextArea value={String(value ?? "")} maxLength={field.validation?.max_length ?? 2000} onChange={onChange} />;

    case "single":
      if (widget === "segmented") {
        return <Segmented options={options} value={value == null ? null : String(value)} onChange={onChange} />;
      }
      if (widget === "select") {
        return <Select options={options} value={value == null ? null : String(value)} onChange={onChange} />;
      }
      return (
        <ChipGroup
          options={options}
          value={value ? [String(value)] : []}
          multi={false}
          onChange={(arr) => onChange(arr[0] ?? null)}
        />
      );

    case "multi":
      return (
        <ChipGroup
          options={options}
          value={Array.isArray(value) ? (value as string[]) : []}
          onChange={(arr) => onChange(arr)}
        />
      );
  }
}