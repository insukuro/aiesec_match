import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchers, qk } from "../../shared/api/queries";
import { ProfileCompleteness } from "../../widgets/ProfileCompleteness";
import { ProfileSummary } from "../../entities/profile/ProfileSummary";
import { ProfileVersionHistory } from "../../widgets/ProfileVersionHistory";
import { Skeleton } from "../../shared/ui/Skeleton";
import { ErrorBanner } from "../../shared/ui/ErrorBanner";
import { Button } from "../../shared/ui/Button";
import { ROUTES } from "../../app/routes";
import { useAuth } from "../../features/auth/AuthContext";
import { GuestBanner } from "../../widgets/GuestBanner";
import { EmptyState } from "../../shared/ui/EmptyState";

export function ProfilePage() {
  const nav = useNavigate();
  const { isGuest } = useAuth();
  useEffect(() => { document.title = "Профиль — AIESEC Match"; }, []);
  const q = useQuery({ queryKey: qk.profile, queryFn: fetchers.profile, retry: 0, enabled: !isGuest });

  if (isGuest) {
    return (
      <main className="page">
        <h1 className="page__title">Профиль</h1>
        <GuestBanner />
        <EmptyState
          title="Создайте аккаунт"
          description="Профиль доступен только в аккаунте."
          action={<Button onClick={() => nav(ROUTES.register)}>Создать аккаунт</Button>}
        />
      </main>
    );
  }

  if (q.isLoading) return <main className="page"><Skeleton lines={8} /></main>;
  if (q.error) return <main className="page"><ErrorBanner error={q.error} onRetry={() => q.refetch()} /></main>;
  if (!q.data) {
    return (
      <main className="page">
        <h1 className="page__title">Профиль</h1>
        <EmptyState
          title="Профиль не заполнен"
          description="Пройдите короткую анкету — это займёт пару минут."
          action={<Button onClick={() => nav(ROUTES.onboarding(0))}>Заполнить</Button>}
        />
      </main>
    );
  }

  const p = q.data;
  return (
    <main className="page">
      <h1 className="page__title">Профиль</h1>
      <ProfileCompleteness completeness={p.completeness} onEdit={() => nav(ROUTES.profileEdit)} />
      <ProfileSummary profile={p} />
      <div className="row section">
        <Button onClick={() => nav(ROUTES.profileEdit)}>Редактировать</Button>
        <Button variant="outline" onClick={() => nav(ROUTES.favorites)}>Избранное</Button>
        <Link to={ROUTES.profileStats} className="ui-btn" data-variant="outline">Моя статистика</Link>
      </div>
      <section className="section">
        <h2 className="section__title">История версий</h2>
        <ProfileVersionHistory />
      </section>
    </main>
  );
  
}