import type { Path } from "react-router-dom";
import { ROUTES } from "../../app/routes";

const returnRoutes = new Map<string, string>([
  [ROUTES.dashboard, ROUTES.dashboard],
  [ROUTES.results, ROUTES.results],
  ["/opportunities", ROUTES.results],
  [ROUTES.profile, ROUTES.profile],
  [ROUTES.profileEdit, ROUTES.profileEdit],
  [ROUTES.favorites, ROUTES.favorites],
  ["/profile/statistics", ROUTES.dashboard],
  ["/profile/statistics/settings", ROUTES.dashboard],
  [ROUTES.history, ROUTES.history],
  [ROUTES.notifications, ROUTES.notifications],
  [ROUTES.settings, ROUTES.settings],
]);

function returnPathname(pathname: string): string | undefined {
  const path = pathname.replace(/\/+$/, "").toLowerCase();
  const route = returnRoutes.get(path);
  if (route) return route;

  const match = /^\/(opportunity|onboarding)\/([0-9]+)$/.exec(path);
  if (!match) return;

  const id = Number(match[2]);
  if (!Number.isSafeInteger(id)) return;

  return match[1] === "opportunity" ? ROUTES.opportunity(id) : ROUTES.onboarding(id);
}

export function loginDestination(next: string | null, hasProfile?: boolean): Partial<Path> {
  const fallback = { pathname: hasProfile ? ROUTES.dashboard : ROUTES.onboarding(0) };
  if (!next?.startsWith("/") || next.startsWith("//")) return fallback;

  const origin = window.location.origin;
  let url: URL;
  try {
    url = new URL(next, origin);
  } catch {
    return fallback;
  }
  if (url.origin !== origin) return fallback;

  const pathname = returnPathname(url.pathname);
  if (!pathname) return fallback;

  return { pathname, search: url.search, hash: url.hash };
}
