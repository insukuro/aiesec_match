import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../shared/api/endpoints";
import { qk } from "../../shared/api/queries";
import { RequirementChips } from "../../entities/opportunity/RequirementChips";
import { CapacityBadge } from "../../entities/opportunity/CapacityBadge";
import { CostLabel } from "../../entities/opportunity/CostLabel";
import { ProgrammeBadge } from "../../entities/opportunity/ProgrammeBadge";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Button } from "../../shared/ui/Button";
import { formatDate } from "../../shared/lib/date";
import { useSendFeedback } from "../../features/feedback/useSendFeedback";

export function OpportunityPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const feedback = useSendFeedback();
  const oppId = Number(id);
  const q = useQuery({
    queryKey: qk.opportunity(oppId),
    queryFn: () => api.getOpportunity(oppId),
    retry: 0,
  });
  useEffect(() => { if (q.data) document.title = `${q.data.title} — AIESEC Match`; }, [q.data]);

  if (q.isLoading) return <main className="page"><Skeleton lines={8} /></main>;
  if (q.error) return <main className="page"><ErrorBanner error={q.error} onRetry={() => q.refetch()} /></main>;
  if (!q.data) return null;
  const o = q.data;

const AIESEC_SLUG: Record<string, string> = {
  talent: "global-talent",
  teacher: "global-teacher",
  volunteer: "global-volunteer",
};

  const onApply = async () => {
    await feedback.mutateAsync({ opportunity_id: o.opportunity_id, signal: "applied" });
    const slug = AIESEC_SLUG[o.programme.kind] ?? "global-talent";
    window.open(
      `https://aiesec.org/opportunity/${slug}/${o.opportunity_id}`,
      "_blank",
      "noopener"
    );
  };

  return (
    <main className="page">
      <Button variant="text" onClick={() => nav(-1)}>← Назад</Button>
      <h1 className="page__title">{o.title}</h1>
      <div className="row">
        <ProgrammeBadge kind={o.programme.kind} />
        <span className="muted">{o.place.country_name} · {o.place.lc_name}</span>
      </div>
      {o.organisation_name && <p className="muted">{o.organisation_name}</p>}

      <div className="row section">
        <CostLabel cost={o.cost} />
        {o.duration_weeks != null && <span>{o.duration_weeks} нед.</span>}
        <CapacityBadge capacity={o.capacity} />
      </div>

      <RequirementChips requirements={o.requirements} />

      <section className="section">
        <h2 className="section__title">Даты</h2>
        <ul className="muted">
          <li>Открыта: {formatDate(o.date_opened)}</li>
          <li>Заявки до: {formatDate(o.applications_close_date)}</li>
          <li>Старт: {formatDate(o.earliest_start_date)}</li>
          <li>Окончание: {formatDate(o.latest_end_date)}</li>
        </ul>
      </section>

      {o.family.siblings_count > 0 && (
        <p className="muted">Ещё {o.family.siblings_count} похожих проектов</p>
      )}

      <Button size="lg" block onClick={onApply} disabled={!o.is_open || feedback.isPending}>
        {o.is_open ? "Откликнуться" : "Набор закрыт"}
      </Button>
    </main>
  );
}