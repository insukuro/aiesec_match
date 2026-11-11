import { Chip } from "../../shared/ui/Chip";

export interface RequirementChipsProps {
  requirements: Array<{ kind: string; name: string; option: string | null }>;
}

export function RequirementChips({ requirements }: RequirementChipsProps) {
  if (requirements.length === 0) return null;
  return (
    <div className="ui-chip-group" style={{ marginTop: "var(--space-2)" }}>
      {requirements.map((r, i) => (
        <Chip key={`${r.kind}-${i}`} selected={r.option === "required"} disabled>
          {r.name}
        </Chip>
      ))}
    </div>
  );
}