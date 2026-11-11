export interface TextAreaProps {
  value: string;
  maxLength?: number;
  onChange: (v: string) => void;
  rows?: number;
}

export function TextArea({ value, maxLength, onChange, rows = 4 }: TextAreaProps) {
  return (
    <div className="ui-textarea">
      <textarea value={value} maxLength={maxLength} rows={rows} onChange={(e) => onChange(e.target.value)} />
      {maxLength && <div className="ui-textarea__hint">{value.length} / {maxLength}</div>}
    </div>
  );
}