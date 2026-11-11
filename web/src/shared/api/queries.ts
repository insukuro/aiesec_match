import { api } from "./endpoints";
import type { AnalyticsPeriod } from "./types";

export const qk = {
  me: ["me"] as const,
  formSchema: ["meta", "form-schema"] as const,
  formOptions: ["meta", "form-options"] as const,
  profile: ["profile"] as const,
  profileVersions: ["profile", "versions"] as const,
  profileVersion: (v: number) => ["profile", "versions", v] as const,
  run: ["run", "latest"] as const,
  runById: (id: string) => ["run", id] as const,
  opportunity: (id: number) => ["opportunity", id] as const,
  opportunities: (params: Record<string, unknown>) => ["opportunities", params] as const,
  subscription: ["subscription"] as const,
  history: (params: Record<string, unknown>) => ["history", params] as const,
  analytics: (period: AnalyticsPeriod, from?: string, to?: string) =>
    ["analytics", period, from ?? null, to ?? null] as const,
  dashboard: ["dashboard-preferences"] as const,
};

export const fetchers = {
  me: api.getMe,
  formSchema: api.getFormSchema,
  formOptions: api.getFormOptions,
  profile: api.getProfile,
  profileVersions: api.listProfileVersions,
  run: api.getLatestRecommendation,
  subscription: api.getSubscription,
  dashboard: api.getDashboardPreferences,
};