import type { FormOption } from "../../shared/api/types";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../../shared/config/brand";

export interface ProgrammeCardsProps {
  options: FormOption[];
  value: string[];
  onChange: (v: string[]) => void;
}

const DESCRIPTIONS: Record<string, string> = {
  talent: "Стажировка в компании за рубежом: 6 недель — 1,5 года.",
  teacher: "Преподавание за рубежом: 6–78 недель, оплачиваемый проект.",
  volunteer: "Волонтёрский проект: 6–8 недель, социальная миссия.",
};

export function ProgrammeCards({ options, value, onChange }: ProgrammeCardsProps) {
  const toggle = (code: string) => {
    onChange(value.includes(code) ? value.filter((c) => c !== code) : [...value, code]);
  };
  return (
    <div className="prog-cards">
      {options.map((o) => {
        const selected = value.includes(o.code);
        const color = PROGRAMME_COLORS[o.code as keyof typeof PROGRAMME_COLORS] ?? "#037EF3";
        return (
          <button
            key={o.code}
            type="button"
            className={`prog-card ${selected ? "prog-card--on" : ""}`}
            style={{ ["--prog-color" as string]: color }}
            onClick={() => toggle(o.code)}
            aria-pressed={selected}
          >
            <div className="prog-card__head">
              <span className="prog-card__check" aria-hidden>{selected ? "✓" : ""}</span>
              <strong>{o.label || PROGRAMME_LABEL[o.code as keyof typeof PROGRAMME_LABEL]}</strong>
            </div>
            <p className="prog-card__desc">{DESCRIPTIONS[o.code] ?? ""}</p>
            {typeof o.count === "number" && (
              <span className="prog-card__count">{o.count} открытых вакансий</span>
            )}
          </button>
        );
      })}
    </div>
  );
}