import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { DashboardCustomizer } from "../../widgets/DashboardCustomizer";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";

export function StatisticsSettingsPage() {
  const nav = useNavigate();
  useEffect(() => { document.title = "Настройки статистики — AIESEC Match"; }, []);
  return (
    <main className="page">
      <Button variant="text" onClick={() => nav(ROUTES.profileStats)}>← Назад</Button>
      <h1 className="page__title">Настройки статистики</h1>
      <DashboardCustomizer />
    </main>
  );
}