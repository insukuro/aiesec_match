import { request } from "./client";
import type {
  AnalyticsPeriod,
  AnalyticsResponse,
  DashboardPreferences,
  FeedbackIn,
  FormOptions,
  FormSchema,
  HistoryEvent,
  LinkCode,
  Me,
  OpportunityCard,
  OpportunityDetail,
  Page,
  ProfileOut,
  ProfileVersionEntry,
  ProfileVersionSnapshot,
  RecommendationRun,
  SubscriptionPrefs,
} from "./types";

export interface AnonymousAuthResponse {
  access_token: string;
  expires_in: number;
  device_secret: string | null;
}

export interface TokenResponse {
  access_token: string;
  expires_in: number;
}

export const api = {
  authAnonymous: (device_secret: string | null) =>
    request<AnonymousAuthResponse>("/auth/anonymous", {
      method: "POST",
      body: { device_secret },
      skipAuth: true,
    }),

  authTelegram: (init_data: string) =>
    request<TokenResponse>("/auth/telegram", {
      method: "POST",
      body: { init_data },
      skipAuth: true,
    }),

  getMe: () => request<Me>("/me"),

  deleteMe: () => request<void>("/me", { method: "DELETE" }),

  postConsent: (kind: "pd_processing" | "marketing", version: string) =>
    request<void>("/me/consents", { method: "POST", body: { kind, version } }),

  createLinkCode: () => request<LinkCode>("/me/link-codes", { method: "POST" }),

  getFormSchema: () => request<FormSchema>("/meta/form-schema"),

  getFormOptions: () => request<FormOptions>("/meta/form-options"),

  getProfile: () => request<ProfileOut>("/profiles/me"),

  putProfile: (body: unknown, ifMatch?: string) =>
    request<ProfileOut>("/profiles/me", { method: "PUT", body, ifMatch }),

  listProfileVersions: () => request<ProfileVersionEntry[]>("/profiles/me/versions"),

  getProfileVersion: (version: number) =>
    request<ProfileVersionSnapshot>(`/profiles/me/versions/${version}`),

  listOpportunities: (params: {
    q?: string;
    programme_kind?: string;
    country_code?: string;
    lc_id?: number;
    family_key?: string;
    only_open?: boolean;
    sort?: "new" | "closing" | "chance";
    limit?: number;
    offset?: number;
  }) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    }
    return request<Page<OpportunityCard>>(`/opportunities?${qs.toString()}`);
  },

  getOpportunity: (id: number) => request<OpportunityDetail>(`/opportunities/${id}`),

  createRecommendations: (idempotencyKey: string, body: { mode: "sync" | "async"; limit_per_programme: number; filters?: Record<string, unknown> }) =>
    request<RecommendationRun>("/recommendations", {
      method: "POST",
      body,
      idempotencyKey,
    }),

  getRecommendation: (runId: string) => request<RecommendationRun>(`/recommendations/${runId}`),

  getLatestRecommendation: () => request<RecommendationRun>("/recommendations/latest"),

  postFeedback: (body: FeedbackIn) => request<void>("/feedback", { method: "POST", body }),

  getSubscription: () => request<SubscriptionPrefs>("/subscriptions/me"),

  putSubscription: (body: SubscriptionPrefs) =>
    request<SubscriptionPrefs>("/subscriptions/me", { method: "PUT", body }),

  getHistory: (params: { type?: string; from?: string; to?: string; limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    }
    return request<Page<HistoryEvent>>(`/history?${qs.toString()}`);
  },

  getAnalytics: (period: AnalyticsPeriod, from?: string, to?: string) => {
    const qs = new URLSearchParams({ period });
    if (from) qs.set("from", from);
    if (to) qs.set("to", to);
    return request<AnalyticsResponse>(`/analytics/me?${qs.toString()}`);
  },

  getDashboardPreferences: () => request<DashboardPreferences>("/users/me/dashboard-preferences"),

  putDashboardPreferences: (body: DashboardPreferences) =>
    request<DashboardPreferences>("/users/me/dashboard-preferences", { method: "PUT", body }),
};