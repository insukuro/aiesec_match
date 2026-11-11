import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { UserStatisticsDashboard } from "../../widgets/UserStatisticsDashboard";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";

export function ProfileStatisticsPage() {
  const nav = useNavigate();
  useEffect(() => { document.title = "Моя статистика — AIESEC Match"; }, []);
  return (
    <main className="page">
      <div className="row" style={{ justifyContent: "space-between", alignItems: "center" }}>
        <h1 className="page__title">Моя статистика</h1>
        <Button variant="outline" onClick={() => nav(ROUTES.profileStatsSettings)}>Настроить</Button>
      </div>
      <UserStatisticsDashboard />
    </main>
  );
}