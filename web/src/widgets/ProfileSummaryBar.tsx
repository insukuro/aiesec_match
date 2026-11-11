import type { ProfileOut } from "../shared/api/types";
import { PROGRAMME_LABEL, PROGRAMME_SHORT } from "../shared/config/brand";
import { Chip } from "../shared/ui/Chip";

export function ProfileSummaryBar({ profile, onEdit }: { profile: ProfileOut; onEdit: () => void }) {
  const chips: string[] = [];
  if (profile.english_level) chips.push(`EN ${profile.english_level}`);
  if (profile.study?.status) chips.push(profile.study.status);
  profile.programmes.forEach((k) => chips.push(PROGRAMME_SHORT[k] ?? PROGRAMME_LABEL[k]));
  return (
    <div className="row" style={{ marginBottom: "var(--space-3)" }}>
      {chips.map((c) => <Chip key={c} selected={false} disabled>{c}</Chip>)}
      <button type="button" className="ui-btn" data-variant="text" onClick={onEdit}>Изменить</button>
    </div>
  );
}