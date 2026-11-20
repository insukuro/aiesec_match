import { request } from "./client";
import type {
  AnalyticsPeriod,
  AnalyticsResponse,
  AuthToken,
  ConsentKind,
  ConsentSchema,
  EmailChangeRequest,
  FeedbackIn,
  FormOptions,
  FormSchema,
  HistoryEvent,
  LinkCode,
  Me,
  NotificationsPage,
  OpportunityCard,
  OpportunityDetail,
  Page,
  ProfileOut,
  ProfileVersionEntry,
  ProfileVersionSnapshot,
  RecommendationRun,
  RecommendationRunSummary,
  SubscriptionPrefs,
} from "./types";

export const api = {
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

  changePassword: (current_password: string, new_password: string) =>
    request<void>("/auth/change-password", {
      method: "POST", body: { current_password, new_password },
    }),

  changeEmail: (new_email: string, password: string) =>
    request<EmailChangeRequest>("/auth/change-email", {
      method: "POST", body: { new_email, password },
    }),

  verifyEmail: (new_email: string, code: string) => {
    const qs = new URLSearchParams({ new_email });
    return request<void>(`/auth/verify-email?${qs.toString()}`, {
      method: "POST", body: { code },
    });
  },

  getMe: () => request<Me>("/me"),
  deleteMe: () => request<void>("/me", { method: "DELETE" }),

  postConsent: (kind: ConsentKind, version: string) =>
    request<void>("/me/consents", { method: "POST", body: { kind, version } }),

  revokeConsent: (kind: "marketing") =>
    request<void>(`/me/consents/${kind}`, { method: "DELETE" }),

  createLinkCode: () => request<LinkCode>("/me/link-codes", { method: "POST" }),

  getFormSchema: () => request<FormSchema>("/meta/form-schema"),
  getConsentSchema: () => request<ConsentSchema>("/meta/consents", { cache: "no-cache" }),
  getFormOptions: () => request<FormOptions>("/meta/form-options"),

  getProfile: () => request<ProfileOut>("/profiles/me"),
  putProfile: (body: unknown, ifMatch?: string) =>
    request<ProfileOut>("/profiles/me", { method: "PUT", body, ifMatch }),

  listProfileVersions: () => request<ProfileVersionEntry[]>("/profiles/me/versions"),
  getProfileVersion: (version: number) =>
    request<ProfileVersionSnapshot>(`/profiles/me/versions/${version}`),

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
  listRecommendationRuns: (params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit !== undefined) qs.set("limit", String(params.limit));
    if (params.offset !== undefined) qs.set("offset", String(params.offset));
    return request<Page<RecommendationRunSummary>>(`/recommendations?${qs.toString()}`);
  },

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

  getNotifications: (params: { limit?: number; offset?: number } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit !== undefined) qs.set("limit", String(params.limit));
    if (params.offset !== undefined) qs.set("offset", String(params.offset));
    return request<NotificationsPage>(`/notifications?${qs.toString()}`);
  },

  markNotificationRead: (notificationId: string) =>
    request<void>(`/notifications/${notificationId}/read`, { method: "POST" }),

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