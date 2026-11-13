import { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../features/auth/AuthContext";
import { setUnauthorizedHandler } from "../shared/api/client";
import { MainNavigation } from "../widgets/MainNavigation";
import { useOnline } from "../shared/hooks/useOnline";
import { Skeleton } from "../shared/ui/Skeleton";

export function App() {
  const nav = useNavigate();
  const location = useLocation();
  const online = useOnline();
  const { state, me } = useAuth();

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

  // Показываем нижнюю навигацию только когда есть пользователь
  // (гость или авторизованный) — не в состоянии "unknown".
  return (
    <>
      <Outlet />
      {me && <MainNavigation />}
    </>
  );
}