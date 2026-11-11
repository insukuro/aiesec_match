import { Progress } from "../shared/ui/Progress";

export function ProfileCompleteness({ completeness, onEdit }: { completeness: number; onEdit: () => void }) {
  const pct = Math.round(completeness * 100);
  return (
    <section className="section">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2 className="section__title">Заполненность</h2>
        <button type="button" className="ui-btn" data-variant="text" onClick={onEdit}>Изменить</button>
      </div>
      <Progress value={completeness} label={`${pct}%`} />
    </section>
  );
}