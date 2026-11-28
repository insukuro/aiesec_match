import { useEffect } from "react";
import { Link, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../features/auth/AuthContext";
import { setUnauthorizedHandler } from "../shared/api/client";
import { fetchers, qk } from "../shared/api/queries";
import { MainNavigation } from "../widgets/MainNavigation";
import { useOnline } from "../shared/hooks/useOnline";
import { ErrorBanner } from "../shared/ui/ErrorBanner";
import { Skeleton } from "../shared/ui/Skeleton";
import { ROUTES } from "./routes";

export function App() {
  const nav = useNavigate();
  const location = useLocation();
  const online = useOnline();
  const { state, me } = useAuth();
  const consents = useQuery({
    queryKey: qk.consents,
    queryFn: fetchers.consents,
    enabled: Boolean(me),
    staleTime: 30_000,
  });

  useEffect(() => {
    setUnauthorizedHandler(() => nav("/login"));
    return () => setUnauthorizedHandler(null);
  }, [nav]);

  useEffect(() => {
    if (!online && !location.pathname.startsWith("/offline")) nav("/offline");
  }, [online, nav, location.pathname]);

  if (state.status === "loading") {
    return (
      <main className="page">
        <Skeleton lines={6} />
      </main>
    );
  }

  const publicRoute = ["/", "/login", "/register", "/offline", "/404"].includes(location.pathname)
    || location.pathname.startsWith("/opportunity/");
  if (!me && !publicRoute) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }
  const requiresProfile = [
    "/app", "/results", "/history", "/profile", "/profile/edit", "/profile/favorites",
  ].includes(location.pathname);
  if (me && !me.has_profile && requiresProfile) {
    return <Navigate to="/onboarding/0" replace />;
  }
  const requiredConsentUpdate = Boolean(me && consents.data?.consents.some(
    (document) => document.required && !me.consents.some(
      (consent) => consent.kind === document.kind && consent.version === document.version,
    ),
  ));
  const consentPageHandlesError = location.pathname === ROUTES.settings
    || location.pathname.startsWith("/onboarding/");

  return (
    <div className="app-shell">
      {me && <MainNavigation />}
      <div className="app-content">
        {me && consents.error && !consentPageHandlesError && (
          <ErrorBanner error={consents.error} onRetry={() => consents.refetch()} />
        )}
        {requiredConsentUpdate && (
          <aside className="ui-card section" role="alert">
            <strong>Мы обновили согласие на обработку персональных данных.</strong>
            <p>
              {location.pathname === ROUTES.settings
                ? "Примите актуальную версию в разделе «Согласия» ниже."
                : <>Чтобы продолжить пользоваться персональным подбором, <Link to={ROUTES.settings}>примите обновлённую версию</Link>.</>}
            </p>
          </aside>
        )}
        <Outlet />
      </div>
    </div>
  );
}
