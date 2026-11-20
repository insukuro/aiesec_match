import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { fetchers, qk } from "../../shared/api/queries";
import { ProfileCompleteness } from "../../widgets/ProfileCompleteness";
import { UserStatisticsDashboard } from "../../widgets/UserStatisticsDashboard";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";

export function ProfileStatisticsPage() {
  const nav = useNavigate();
  const profile = useQuery({ queryKey: qk.profile, queryFn: fetchers.profile, retry: 0 });
  useEffect(() => { document.title = "Обзор — AIESEC Match"; }, []);
  return (
    <main className="page">
      <header className="dashboard-heading">
        <div>
          <h1 className="page__title">Обзор</h1>
          <p className="muted">Ваш профиль и активность в AIESEC Match</p>
        </div>
        <Button onClick={() => nav(ROUTES.results)}>Перейти к подбору</Button>
      </header>
      {profile.data && (
        <ProfileCompleteness
          completeness={profile.data.completeness}
          onEdit={() => nav(ROUTES.profileEdit)}
        />
      )}
      <UserStatisticsDashboard />
    </main>
  );
}