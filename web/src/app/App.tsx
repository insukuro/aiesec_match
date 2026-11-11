import { useEffect } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchers, qk } from "../shared/api/queries";
import { setUnauthorizedHandler } from "../shared/api/client";
import { MainNavigation } from "../widgets/MainNavigation";
import { useOnline } from "../shared/hooks/useOnline";

export function App() {
  const nav = useNavigate();
  const location = useLocation();
  const online = useOnline();

  useEffect(() => {
    setUnauthorizedHandler(() => {
      if (!location.pathname.startsWith("/onboarding")) {
        nav("/login");
      }
    });
    return () => setUnauthorizedHandler(null);
  }, [nav, location.pathname]);

  useEffect(() => {
    if (!online && !location.pathname.startsWith("/offline")) nav("/offline");
  }, [online, nav, location.pathname]);

  const { data: me } = useQuery({
    queryKey: qk.me,
    queryFn: fetchers.me,
    retry: 0,
    staleTime: 60_000,
  });

  return (
    <>
      <Outlet />
      {me && <MainNavigation />}
    </>
  );
}