import { api } from "./endpoints";
import type { AnalyticsPeriod } from "./types";

export const qk = {
  me: ["me"] as const,
  formSchema: ["meta", "form-schema"] as const,
  consents: ["meta", "consents"] as const,
  formOptions: ["meta", "form-options"] as const,
  profile: ["profile"] as const,
  profileVersions: ["profile", "versions"] as const,
  profileVersion: (v: number) => ["profile", "versions", v] as const,
  run: ["run", "latest"] as const,
  runById: (id: string) => ["run", id] as const,
  runs: (params: Record<string, unknown>) => ["runs", params] as const,
  opportunity: (id: number) => ["opportunity", id] as const,
  subscription: ["subscription"] as const,
  notificationsRoot: ["notifications"] as const,
  notifications: (params: Record<string, unknown>) => ["notifications", params] as const,
  historyRoot: ["history"] as const,
  history: (params: Record<string, unknown>) => ["history", params] as const,
  analyticsRoot: ["analytics"] as const,
  analytics: (period: AnalyticsPeriod, from?: string, to?: string) =>
    ["analytics", period, from ?? null, to ?? null] as const,
  liked: (params: Record<string, unknown>) => ["feedback", "liked", params] as const,
  hidden: (params: Record<string, unknown>) => ["feedback", "hidden", params] as const,
};

export const fetchers = {
  me: api.getMe,
  formSchema: api.getFormSchema,
  consents: api.getConsentSchema,
  formOptions: api.getFormOptions,
  profile: api.getProfile,
  profileVersions: api.listProfileVersions,
  run: api.getLatestRecommendation,
  subscription: api.getSubscription,
};