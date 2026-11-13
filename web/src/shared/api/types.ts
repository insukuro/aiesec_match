export type ProgrammeKind = "talent" | "teacher" | "volunteer";
export type MatchLabel = "excellent" | "good" | "fair";

export interface Problem {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  request_id?: string;
  errors?: Array<{ loc: Array<string | number>; msg?: string }>;
}

export interface Me {
  user_id: string;
  is_anonymous: boolean;
  email: string | null;
  has_profile: boolean;
  profile_version: number | null;
  identities: Array<{ provider: string; external_id: string | null }>;
  consents: Array<{ kind: string; version: string; accepted_at: string }>;
}

export interface ProfileData {
  programmes: ProgrammeKind[];
  birth_date: string | null;
  city: string | null;
  preferred_lc_ids: number[] | null;
  study: { status?: string; course?: number; specialty_text?: string } | null;
  english_level: "A1" | "A2" | "B1" | "B2" | "C1" | "C2" | null;
  other_languages: string[] | null;
  work_experience: "none" | "1_2_years" | "3_5_years" | "5_plus_years" | null;
  spheres: string[] | null;
  activities: string[] | null;
  desired_countries: string[] | null;
  duration: { min_weeks?: number; max_weeks?: number } | null;
  start_window: string | null;
  financial: { willing_to_pay: boolean; max_budget_eur?: number; needs_stipend: boolean } | null;
  abroad_experience: boolean | null;
  nationality: string | null;
  experience_text: string | null;
  motivation_text: string | null;
}

export interface ProfileOut extends ProfileData {
  profile_version: number;
  age_years: number | null;
  completeness: number;
  updated_at: string;
}

export interface FormOption {
  code: string;
  label: string;
  description?: string;
  count?: number;
  disabled?: boolean;
}

export type Condition =
  | { any: Condition[] }
  | { all: Condition[] }
  | { field: string; op: "eq" | "in" | "not_in" | "empty" | "not_empty"; value?: unknown };

export interface FormField {
  id: string;
  kind: "single" | "multi" | "text" | "textarea" | "number" | "date" | "boolean";
  label: string;
  help?: string;
  required?: boolean;
  options_source?: string;
  options?: FormOption[];
  validation?: { min?: number; max?: number; max_length?: number; pattern?: string };
  show_if?: Condition;
  maps_to?: string;
  default?: unknown;
  ui?: { widget?: "cards" | "chips" | "select" | "segmented" | "stepper" };
}

export interface FormStep {
  id: string;
  title: string;
  description?: string;
  show_if?: Condition;
  fields: FormField[];
}

export interface FormSchema {
  version: string;
  steps: FormStep[];
}

export type FormOptions = Record<string, FormOption[]>;

export interface OpportunityCard {
  opportunity_id: number;
  title: string;
  family_key: string | null;
  programme: { id: number; kind: ProgrammeKind; name: string };
  place: { country_code: string; country_name: string; lc_id: number; lc_name: string; location: string };
  organisation_name: string | null;
  capacity: { openings: number; available_openings: number; applicants_count: number; accepted_count: number };
  duration_weeks: number | null;
  cost: { amount: number; currency: string } | null;
  requirements: Array<{ kind: string; constant_id: number; name: string; parent_name: string | null; option: string | null }>;
  date_opened: string | null;
  applications_close_date: string | null;
  is_open: boolean;
  updated_at: string;
}

export interface OpportunityDetail extends OpportunityCard {
  earliest_start_date: string | null;
  latest_end_date: string | null;
  experience_type: string | null;
  close_reason: string | null;
  family: { family_key: string | null; siblings_count: number };
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface RecItem {
  rank: number;
  score: number;
  label: MatchLabel;
  family: { family_key: string | null; siblings_count: number };
  opportunity: OpportunityCard;
  reasons: Array<{ code: string; polarity: "positive" | "negative"; weight: number; text: string }>;
}

export interface RecGroup {
  programme_kind: ProgrammeKind;
  total_candidates: number;
  items: RecItem[];
}

export interface RecommendationRun {
  run_id: string;
  state: "queued" | "running" | "succeeded" | "failed";
  profile_version: number;
  strategy: string | null;
  created_at: string;
  finished_at: string | null;
  catalog_watermark: string | null;
  programme_prior: ProgrammeKind[];
  degraded: boolean;
  groups: RecGroup[];
  error: string | null;
}

export interface FeedbackIn {
  opportunity_id: number;
  signal: "opened" | "liked" | "disliked" | "hidden" | "applied";
  run_id?: string | null;
}

export interface SubscriptionPrefs {
  notify_new_matches: boolean;
  min_score: number;
  channels: Array<"telegram">;
}

export interface LinkCode {
  code: string;
  expires_in: number;
}

export interface ProfileVersionEntry {
  version: number;
  created_at: string;
  completeness: number;
}

export interface ProfileVersionSnapshot extends ProfileOut {
  version: number;
  created_at: string;
}

export type HistoryType =
  | "profile_created" | "profile_updated" | "run_started" | "run_finished"
  | "opportunity_viewed" | "signal_liked" | "signal_disliked" | "signal_hidden" | "signal_applied";

export interface HistoryEvent {
  event_id: string;
  type: HistoryType;
  occurred_at: string;
  title: string;
  description?: string;
  related_entity_id?: string | null;
  metadata?: Record<string, unknown>;
}

export type AnalyticsPeriod = "7d" | "30d" | "90d" | "all";

export interface AnalyticsResponse {
  profile_completeness: { percent: number; filled: number; total: number };
  programme_distribution: Array<{ programme_kind: ProgrammeKind; count: number }>;
  interests_distribution: Array<{ code: string; label: string; count: number }>;
  activity_series: Array<{ bucket: string; run_started: number; viewed: number; liked: number; applied: number }>;
  recommendation_statistics: Array<{ programme_kind: ProgrammeKind; count: number }>;
}

export interface DashboardPreferences {
  visible_charts: string[];
  order: string[];
  period: AnalyticsPeriod;
  chart_types: Record<string, string>;
}

export const CHART_IDS = [
  "profile_completeness", "programme_distribution", "interests_distribution",
  "activity_series", "recommendation_statistics",
] as const;
export type ChartId = (typeof CHART_IDS)[number];

export const DEFAULT_DASHBOARD: DashboardPreferences = {
  visible_charts: [...CHART_IDS],
  order: [...CHART_IDS],
  period: "30d",
  chart_types: {},
};

export interface AuthToken {
  access_token: string;
  expires_in: number;
  is_anonymous: boolean;
  device_secret?: string | null;
}