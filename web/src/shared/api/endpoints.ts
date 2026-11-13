import { request } from "./client";
import type {
  AnalyticsPeriod,
  AnalyticsResponse,
  AuthToken,
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

export const api = {
  authAnonymous: (device_secret: string | null) =>
    request<AuthToken>("/auth/anonymous", {
      method: "POST", body: { device_secret }, skipAuth: true,
    }),

  authRegister: (email: string, password: string) =>
    request<AuthToken>("/auth/register", {
      method: "POST", body: { email, password }, skipAuth: true,
    }),

  authLogin: (email: string, password: string) =>
    request<AuthToken>("/auth/login", {
      method: "POST", body: { email, password }, skipAuth: true,
    }),

  authTelegram: (init_data: string) =>
    request<AuthToken>("/auth/telegram", {
      method: "POST", body: { init_data }, skipAuth: true,
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

  listOpportunities: (params: Record<string, string | number | boolean | undefined>) => {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== "") qs.set(k, String(v));
    }
    return request<Page<OpportunityCard>>(`/opportunities?${qs.toString()}`);
  },

  getOpportunity: (id: number) => request<OpportunityDetail>(`/opportunities/${id}`),

  createRecommendations: (
    idempotencyKey: string,
    body: { mode: "sync" | "async"; limit_per_programme: number; filters?: Record<string, unknown> },
  ) =>
    request<RecommendationRun>("/recommendations", {
      method: "POST", body, idempotencyKey,
    }),

  getRecommendation: (runId: string) => request<RecommendationRun>(`/recommendations/${runId}`),
  getLatestRecommendation: () => request<RecommendationRun>("/recommendations/latest"),

  getSubscription: () => request<SubscriptionPrefs>("/subscriptions/me"),
  putSubscription: (body: SubscriptionPrefs) =>
    request<SubscriptionPrefs>("/subscriptions/me", { method: "PUT", body }),

  getHistory: (params: Record<string, string | number | undefined>) => {
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
    postFeedback: (body: FeedbackIn) => request<void>("/feedback", { method: "POST", body }),

  deleteFeedback: (opportunityId: number, signal: "liked" | "disliked" | "hidden" | "opened" | "applied") =>
    request<void>(`/feedback/${opportunityId}?signal=${signal}`, { method: "DELETE" }),

  getLikedFeedback: (params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    return request<Page<OpportunityCard>>(`/feedback/liked?${qs.toString()}`);
  },

  getHiddenFeedback: (params?: { limit?: number; offset?: number }) => {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.offset) qs.set("offset", String(params.offset));
    return request<Page<OpportunityCard>>(`/feedback/hidden?${qs.toString()}`);
  },
};