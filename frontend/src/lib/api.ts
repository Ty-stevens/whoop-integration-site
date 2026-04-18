export class ApiError extends Error {
  status: number;
  details: unknown;

  constructor(message: string, status: number, details: unknown) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function defaultApiBaseUrl() {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Vercel Services mounts the FastAPI service at /backend in this project.
  if (typeof window !== "undefined" && window.location.hostname.endsWith(".vercel.app")) {
    return "/backend";
  }
  return "";
}

const apiBaseUrl = defaultApiBaseUrl();
const apiAuthToken = import.meta.env.VITE_API_AUTH_TOKEN ?? "";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined)
  };
  if (apiAuthToken) {
    headers["X-API-Key"] = apiAuthToken;
  }

  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers,
    ...init
  });

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError("Request failed", response.status, body);
  }

  if (!isJson) {
    throw new ApiError("Expected JSON response from API", response.status, body);
  }

  return body as T;
}

export type HealthResponse = {
  app: string;
  status: string;
  environment: string;
  version: string;
  database: boolean;
};

export type WhoopStatus = {
  status: "disconnected" | "connected" | "expired" | "error" | "config_missing";
  credentials_configured: boolean;
  connected_at_utc: string | null;
  last_token_refresh_at_utc: string | null;
  token_expires_at_utc: string | null;
  granted_scopes: string | null;
  message: string;
};

export type AppSettings = {
  auto_sync_enabled: boolean;
  auto_sync_frequency: "daily" | "twice_daily";
  preferred_export_format: "csv";
  preferred_units: "metric" | "imperial";
};

export type AthleteProfile = {
  display_name: string | null;
  gender: string | null;
  date_of_birth: string | null;
  age_years: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  training_focus: string | null;
  experience_level: "beginner" | "intermediate" | "advanced" | "elite" | null;
  notes_for_ai: string | null;
  ai_context_allowed: boolean;
};

export type ZoneProgress = {
  zone: number;
  actual_seconds: number;
  actual_minutes: number;
  target_minutes: number;
  percent_complete: number | null;
  remaining_minutes: number;
  exceeded: boolean;
};

export type SessionProgress = {
  completed: number;
  target: number;
  remaining: number;
  percent_complete: number | null;
};

export type CurrentWeekDashboard = {
  week_start_date: string;
  week_end_date: string;
  has_goal_profile: boolean;
  goal_profile_id: number | null;
  last_successful_sync_at_utc: string | null;
  zones: ZoneProgress[];
  cardio_sessions: SessionProgress;
  strength_sessions: SessionProgress;
  total_training_seconds: number;
  average_recovery_score: number | null;
  average_daily_strain: number | null;
};

export type SyncCounts = {
  inserted: number;
  updated: number;
  unchanged: number;
  failed: number;
};

export type SyncRunSummary = {
  id: number;
  resource_type: string | null;
  trigger: string;
  status: string;
  window_start_utc: string | null;
  window_end_utc: string | null;
  inserted_count: number;
  updated_count: number;
  unchanged_count: number;
  failed_count: number;
  started_at_utc: string | null;
  finished_at_utc: string | null;
  error_message: string | null;
};

export type SyncResourceOutcome = {
  resource_type: "workouts" | "sleeps" | "recoveries";
  status: string;
  counts: SyncCounts;
  run_id: number;
  window_start_utc: string;
  window_end_utc: string;
  error_message: string | null;
};

export type SyncStatus = {
  status: "idle" | "running" | "success" | "partial" | "failed";
  auto_sync_enabled: boolean;
  auto_sync_frequency: "daily" | "twice_daily";
  last_success_at_utc: string | null;
  latest_run: SyncRunSummary | null;
  outcomes: SyncResourceOutcome[];
  counts: SyncCounts;
  message: string;
};

export type GoalProfile = {
  id: number;
  effective_from_date: string;
  effective_to_date: string | null;
  zone1_target_minutes: number;
  zone2_target_minutes: number;
  zone3_target_minutes: number;
  zone4_target_minutes: number;
  zone5_target_minutes: number;
  cardio_sessions_target: number;
  strength_sessions_target: number;
  created_reason: string | null;
  created_at_utc: string;
};

export type ActiveGoalProfileResponse = {
  profile: GoalProfile | null;
  message: string;
};

export type GoalProfileListResponse = {
  profiles: GoalProfile[];
};

export type GoalProfileCreateInput = {
  effective_from_date: string;
  effective_to_date?: string | null;
  zone1_target_minutes?: number;
  zone2_target_minutes?: number;
  zone3_target_minutes?: number;
  zone4_target_minutes?: number;
  zone5_target_minutes?: number;
  cardio_sessions_target?: number;
  strength_sessions_target?: number;
  created_reason?: string | null;
};

export type TrendWeeklyPoint = {
  week_start_date: string;
  week_end_date: string;
  workout_count: number;
  sleep_count: number;
  recovery_count: number;
  average_recovery_score: number | null;
  average_daily_strain: number | null;
  recovery_per_strain: number | null;
};

export type RollingComparisonCard = {
  metric: "recovery" | "strain";
  label: string;
  current_window_start_date: string;
  current_window_end_date: string;
  previous_window_start_date: string;
  previous_window_end_date: string;
  current_average: number | null;
  previous_average: number | null;
  delta: number | null;
  direction: "up" | "down" | "flat" | "insufficient";
  has_enough_history: boolean;
};

export type RecoveryStrainTrends = {
  range_start_week: string;
  range_end_week: string;
  weekly_series: TrendWeeklyPoint[];
  comparison_cards: RollingComparisonCard[];
  interpretation_text: string;
  data_state: "empty" | "partial" | "ready";
};

export type MonthlyTrainingSummary = {
  month_start_date: string;
  month_end_date: string;
  month_label: string;
  workout_count: number;
  sleep_count: number;
  recovery_count: number;
  training_seconds: number;
  zone1_minutes: number;
  zone2_minutes: number;
  zone3_minutes: number;
  zone4_minutes: number;
  zone5_minutes: number;
  cardio_count: number;
  strength_count: number;
  other_count: number;
  unknown_count: number;
  average_recovery_score: number | null;
  average_daily_strain: number | null;
};

export type ConsistencySummary = {
  weeks_in_range: number;
  active_weeks: number;
  weeks_with_workouts: number;
  weeks_with_sleeps: number;
  weeks_with_recoveries: number;
  training_week_coverage_percent: number | null;
  sleep_week_coverage_percent: number | null;
  recovery_week_coverage_percent: number | null;
  summary_text: string;
};

export type SixMonthReport = {
  range_start_date: string;
  range_end_date: string;
  month_count: number;
  monthly_summaries: MonthlyTrainingSummary[];
  consistency_summary: ConsistencySummary;
};

export type Classification = "cardio" | "strength" | "other" | "unknown";
export type StrengthSplit = "upper" | "lower" | "full" | "unknown";

export type WorkoutAnnotation = {
  manual_classification: Classification | null;
  manual_strength_split: StrengthSplit | null;
  tag: string | null;
  notes: string | null;
  updated_at_utc: string | null;
};

export type WorkoutSummary = {
  id: number;
  local_start_date: string;
  start_time_utc: string;
  sport_name: string | null;
  score_state: string | null;
  classification: Classification;
  effective_classification: Classification;
  duration_seconds: number;
  strain: number | null;
  average_hr: number | null;
  max_hr: number | null;
  zone1_seconds: number;
  zone2_seconds: number;
  zone3_seconds: number;
  zone4_seconds: number;
  zone5_seconds: number;
  annotation: WorkoutAnnotation | null;
};

export type RecentWorkoutsResponse = {
  workouts: WorkoutSummary[];
};

export type WorkoutAnnotationInput = {
  manual_classification: Classification | null;
  manual_strength_split: StrengthSplit | null;
  tag: string | null;
  notes: string | null;
};

export type StrengthSplitCount = {
  split: "upper" | "lower" | "full" | "unknown" | "untagged";
  count: number;
};

export type StrengthPeriodCount = {
  period_start_date: string;
  label: string;
  count: number;
};

export type StrengthOverview = {
  range_start_date: string;
  range_end_date: string;
  strength_sessions: number;
  strength_strain: number | null;
  split_counts: StrengthSplitCount[];
  weekly_counts: StrengthPeriodCount[];
  monthly_counts: StrengthPeriodCount[];
  untagged_sessions: number;
};

export type AiStatus = {
  status: "disabled" | "configured" | "reachable" | "failing";
  provider: "disabled" | "openai_compatible" | "openclaw";
  enabled: boolean;
  model: string | null;
  message: string;
};

export type AiWeeklySummary = {
  status: "disabled" | "success" | "error";
  summary: string | null;
  observations: string[];
  generated_at_utc: string;
  message: string;
};

export type AiGoalSuggestion = GoalProfileCreateInput & {
  rationale: string;
  confidence: string;
};

export type AiGoalSuggestionsResponse = {
  status: "disabled" | "success" | "error";
  suggestions: AiGoalSuggestion[];
  generated_at_utc: string;
  message: string;
};
