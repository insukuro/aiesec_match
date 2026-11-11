import type { ProfileOut } from "../../shared/api/types";
import { PROGRAMME_COLORS, PROGRAMME_LABEL } from "../../shared/config/brand";

export function ProfileSummary({ profile }: { profile: ProfileOut }) {
  const rows: Array<[string, string]> = [];
  if (profile.city) rows.push(["Город", profile.city]);
  if (profile.age_years != null) rows.push(["Возраст", String(profile.age_years)]);
  if (profile.study?.status) rows.push(["Обучение", profile.study.status]);
  if (profile.study?.course) rows.push(["Курс", String(profile.study.course)]);
  if (profile.study?.specialty_text) rows.push(["Специальность", profile.study.specialty_text]);
  if (profile.english_level) rows.push(["Английский", profile.english_level]);
  if (profile.other_languages?.length) rows.push(["Другие языки", profile.other_languages.join(", ")]);
  if (profile.work_experience) rows.push(["Опыт работы", profile.work_experience]);
  if (profile.desired_countries?.length) rows.push(["Страны", profile.desired_countries.join(", ")]);
  if (profile.duration?.max_weeks) rows.push(["Срок", `до ${profile.duration.max_weeks} нед.`]);
  if (profile.financial?.willing_to_pay) rows.push(["Готов платить", profile.financial.max_budget_eur ? `до ${profile.financial.max_budget_eur} €` : "да"]);
  if (profile.abroad_experience != null) rows.push(["Опыт за границей", profile.abroad_experience ? "да" : "нет"]);

  return (
    <section className="section">
      {profile.programmes.length > 0 && (
        <div className="row" style={{ marginBottom: "var(--space-3)" }}>
          {profile.programmes.map((k) => (
            <span key={k} className="ui-badge" style={{ background: PROGRAMME_COLORS[k], color: "#fff" }}>
              {PROGRAMME_LABEL[k]}
            </span>
          ))}
        </div>
      )}
      <dl className="stack" style={{ margin: 0 }}>
        {rows.map(([k, v]) => (
          <div key={k} className="row" style={{ justifyContent: "space-between" }}>
            <dt className="muted">{k}</dt>
            <dd style={{ margin: 0, fontWeight: 600 }}>{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}