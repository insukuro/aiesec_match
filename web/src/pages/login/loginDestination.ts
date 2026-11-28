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

export function loginDestination(next: string | null, hasProfile?: boolean): string {
  const fallback = hasProfile ? ROUTES.dashboard : ROUTES.onboarding(0);
  if (!next) return fallback;

  const path = next.replace(/\/+$/, "").toLowerCase();
  const route = returnRoutes.get(path);
  if (route) return route;

  const match = /^\/(opportunity|onboarding)\/([0-9]+)$/.exec(path);
  if (!match) return fallback;

  const id = Number(match[2]);
  if (!Number.isSafeInteger(id)) return fallback;

  return match[1] === "opportunity" ? ROUTES.opportunity(id) : ROUTES.onboarding(id);
}
