export const ROUTES = {
  welcome: "/",
  register: "/register",
  login: "/login",
  onboarding: (step: number) => `/onboarding/${step}`,
  results: "/results",
  opportunity: (id: number) => `/opportunity/${id}`,
  profile: "/profile",
  profileEdit: "/profile/edit",
  profileStats: "/profile/statistics",
  profileStatsSettings: "/profile/statistics/settings",
  history: "/history",
  settings: "/settings",
} as const;