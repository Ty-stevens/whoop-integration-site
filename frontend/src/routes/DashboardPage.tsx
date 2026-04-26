import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PageHeader } from "../components/ui/PageHeader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionShell } from "../components/ui/SectionShell";
import { StatBlock } from "../components/ui/StatBlock";
import { apiFetch, type AiWeeklySummary, type CurrentWeekDashboard, type SyncStatus } from "../lib/api";
import { formatDateRangeLabel, formatLongDate } from "../lib/dates";
import { minutesLabel } from "../lib/format";
import { zoneColors, zoneLabels } from "../lib/zones";

function isSessionProgress(value: unknown): value is CurrentWeekDashboard["cardio_sessions"] {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.completed === "number" &&
    typeof candidate.target === "number" &&
    typeof candidate.remaining === "number"
  );
}

function isDashboardPayload(value: unknown): value is CurrentWeekDashboard {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.week_start_date === "string" &&
    typeof candidate.week_end_date === "string" &&
    Array.isArray(candidate.zones) &&
    isSessionProgress(candidate.cardio_sessions) &&
    isSessionProgress(candidate.strength_sessions) &&
    typeof candidate.total_training_seconds === "number"
  );
}

function isSyncPayload(value: unknown): value is SyncStatus {
  if (!value || typeof value !== "object") {
    return false;
  }
  const candidate = value as Record<string, unknown>;
  if (!candidate.counts || typeof candidate.counts !== "object") {
    return false;
  }
  const counts = candidate.counts as Record<string, unknown>;
  return (
    typeof candidate.status === "string" &&
    typeof candidate.message === "string" &&
    typeof candidate.auto_sync_enabled === "boolean" &&
    typeof counts.inserted === "number" &&
    typeof counts.updated === "number" &&
    typeof counts.unchanged === "number" &&
    typeof counts.failed === "number"
  );
}

function formatPercent(value: number | null) {
  return value === null ? "—" : `${Math.round(value)}%`;
}

function formatSharePercent(value: number) {
  if (value > 0 && value < 1) {
    return "<1%";
  }
  return `${Math.round(value)}%`;
}

function formatSeconds(seconds: number) {
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) {
    return `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder > 0 ? `${hours} hr ${remainder} min` : `${hours} hr`;
}

function syncBadge(status: SyncStatus["status"]) {
  if (status === "running") {
    return "Running";
  }
  if (status === "success") {
    return "Success";
  }
  if (status === "partial") {
    return "Partial";
  }
  if (status === "failed") {
    return "Failed";
  }
  return "Idle";
}

function zoneShare(zone: CurrentWeekDashboard["zones"][number], totalZoneSeconds: number) {
  if (totalZoneSeconds <= 0) {
    return 0;
  }
  return (zone.actual_seconds / totalZoneSeconds) * 100;
}

function zoneProgressValue(zone: CurrentWeekDashboard["zones"][number], totalZoneSeconds: number) {
  if (zone.percent_complete !== null) {
    return zone.percent_complete;
  }
  const share = zoneShare(zone, totalZoneSeconds);
  return zone.actual_seconds > 0 ? Math.max(share, 2) : 0;
}

function zoneHeaderText(zone: CurrentWeekDashboard["zones"][number]) {
  if (zone.target_minutes > 0) {
    return formatPercent(zone.percent_complete);
  }
  return minutesLabel(zone.actual_minutes);
}

function zoneDetailText(zone: CurrentWeekDashboard["zones"][number]) {
  if (zone.target_minutes > 0) {
    return `${minutesLabel(zone.actual_minutes)} of ${minutesLabel(zone.target_minutes)}`;
  }
  return `${minutesLabel(zone.actual_minutes)} logged`;
}

function zoneStatusText(zone: CurrentWeekDashboard["zones"][number], totalZoneSeconds: number) {
  if (zone.target_minutes === 0) {
    if (zone.actual_seconds <= 0) {
      return "No time logged";
    }
    return `${formatSharePercent(zoneShare(zone, totalZoneSeconds))} of HR zone time`;
  }

  if (zone.remaining_minutes > 0) {
    return `${minutesLabel(zone.remaining_minutes)} remaining`;
  }

  const overTargetMinutes = Math.max(zone.actual_minutes - zone.target_minutes, 0);
  if (zone.exceeded && overTargetMinutes > 0) {
    return `${minutesLabel(overTargetMinutes)} over target`;
  }

  return "On target";
}

export function DashboardPage() {
  const queryClient = useQueryClient();

  const dashboardQuery = useQuery({
    queryKey: ["dashboard", "current-week"],
    queryFn: () => apiFetch<CurrentWeekDashboard>("/api/v1/dashboard/current-week")
  });

  const syncStatusQuery = useQuery({
    queryKey: ["sync-status"],
    queryFn: () => apiFetch<SyncStatus>("/api/v1/sync/status")
  });

  const manualRefresh = useMutation({
    mutationFn: () => apiFetch<SyncStatus>("/api/v1/sync/run", { method: "POST", body: JSON.stringify({}) }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["dashboard", "current-week"] }),
        queryClient.invalidateQueries({ queryKey: ["sync-status"] })
      ]);
    }
  });

  const aiSummary = useMutation({
    mutationFn: () => apiFetch<AiWeeklySummary>("/api/v1/ai/weekly-summary", { method: "POST" })
  });

  const dashboardData = isDashboardPayload(dashboardQuery.data) ? dashboardQuery.data : null;
  const syncData = isSyncPayload(syncStatusQuery.data) ? syncStatusQuery.data : null;
  const totalZoneSeconds = dashboardData?.zones.reduce((total, zone) => total + zone.actual_seconds, 0) ?? 0;

  const weekLabel = dashboardData
    ? formatDateRangeLabel(dashboardData.week_start_date, dashboardData.week_end_date)
    : "Current ISO week";

  return (
    <>
      <PageHeader title="Current Week" eyebrow="Dashboard">
        <div className="text-sm text-muted">{weekLabel}</div>
      </PageHeader>

      {dashboardQuery.isLoading ? <LoadingState message="Loading current week metrics" /> : null}
      {dashboardQuery.isError ? <ErrorState message="Current week metrics are unavailable right now." /> : null}
      {dashboardQuery.isSuccess && !dashboardData ? (
        <ErrorState message="Dashboard response was invalid. Check backend deployment config." />
      ) : null}
      {syncStatusQuery.isLoading ? <LoadingState message="Loading sync status" /> : null}
      {syncStatusQuery.isError ? <ErrorState message="Sync status is unavailable right now." /> : null}
      {syncStatusQuery.isSuccess && !syncData ? (
        <ErrorState message="Sync status response was invalid. Check backend deployment config." />
      ) : null}

      {dashboardData ? (
        <>
          <div className="grid gap-4 lg:grid-cols-4">
            <Card className="lg:col-span-2">
              <StatBlock
                label="Weekly training"
                value={formatSeconds(dashboardData.total_training_seconds)}
                hint={`Week start ${formatLongDate(dashboardData.week_start_date)}`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Cardio sessions"
                value={`${dashboardData.cardio_sessions.completed} / ${dashboardData.cardio_sessions.target}`}
                hint={`${dashboardData.cardio_sessions.remaining} remaining`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Strength sessions"
                value={`${dashboardData.strength_sessions.completed} / ${dashboardData.strength_sessions.target}`}
                hint={`${dashboardData.strength_sessions.remaining} remaining`}
              />
            </Card>
          </div>

          <SectionShell title="HR Zone Progress">
            <div className="grid gap-4 lg:grid-cols-5">
              {dashboardData.zones.map((zone) => (
                <Card key={zone.zone}>
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <p className="font-semibold">{zoneLabels[`zone${zone.zone}` as keyof typeof zoneLabels]}</p>
                    <span className="text-sm text-muted">{zoneHeaderText(zone)}</span>
                  </div>
                  <ProgressBar value={zoneProgressValue(zone, totalZoneSeconds)} color={zoneColors[`zone${zone.zone}` as keyof typeof zoneColors]} />
                  <p className="mt-3 text-sm text-muted">
                    {zoneDetailText(zone)}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    {zoneStatusText(zone, totalZoneSeconds)}
                  </p>
                </Card>
              ))}
            </div>
          </SectionShell>

          <SectionShell title="Recovery And Strain">
            <div className="grid gap-4 lg:grid-cols-3">
              <Card>
                <StatBlock
                  label="Average recovery"
                  value={dashboardData.average_recovery_score === null ? "—" : Math.round(dashboardData.average_recovery_score).toString()}
                  hint="Backend-derived from synced recovery records"
                />
              </Card>
              <Card>
                <StatBlock
                  label="Average daily strain"
                  value={dashboardData.average_daily_strain === null ? "—" : Math.round(dashboardData.average_daily_strain).toString()}
                  hint="Backend-derived from synced workout records"
                />
              </Card>
              <Card>
                <StatBlock
                  label="Goal profile"
                  value={dashboardData.has_goal_profile ? `#${dashboardData.goal_profile_id}` : "Unset"}
                  hint={dashboardData.has_goal_profile ? "Active for this week" : "No active goal profile"}
                />
              </Card>
            </div>
          </SectionShell>

          <SectionShell title="Advisory Summary">
            <Card>
              <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                <div>
                  <p className="font-semibold">Training readout</p>
                  <p className="mt-1 text-sm text-muted">
                    AI stays off unless the server is configured, and summaries are advisory only.
                  </p>
                  {aiSummary.data ? (
                    <div className="mt-4 text-sm">
                      <p className="font-semibold">{aiSummary.data.message}</p>
                      {aiSummary.data.summary ? (
                        <p className="mt-2 whitespace-pre-wrap text-muted">{aiSummary.data.summary}</p>
                      ) : null}
                    </div>
                  ) : null}
                  {aiSummary.isError ? (
                    <p className="mt-3 text-sm text-red-200">AI summary is unavailable.</p>
                  ) : null}
                </div>
                <Button disabled={aiSummary.isPending} onClick={() => aiSummary.mutate()}>
                  {aiSummary.isPending ? "Generating" : "Generate summary"}
                </Button>
              </div>
            </Card>
          </SectionShell>
        </>
      ) : null}

      <SectionShell title="Sync Status">
        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            {syncData ? (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold">{syncBadge(syncData.status)}</p>
                    <p className="mt-1 text-sm text-muted">{syncData.message}</p>
                  </div>
                  <Button disabled={manualRefresh.isPending} onClick={() => manualRefresh.mutate()}>
                    {manualRefresh.isPending ? "Refreshing" : "Refresh now"}
                  </Button>
                </div>
                <div className="grid gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <p className="text-muted">Auto sync</p>
                    <p className="font-semibold">
                      {syncData.auto_sync_enabled ? syncData.auto_sync_frequency : "Disabled"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted">Last success</p>
                    <p className="font-semibold">
                      {syncData.last_success_at_utc
                        ? formatLongDate(syncData.last_success_at_utc.slice(0, 10))
                        : "None yet"}
                    </p>
                  </div>
                </div>
                <div className="grid gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <p className="text-muted">Inserted</p>
                    <p className="font-semibold">{syncData.counts.inserted}</p>
                  </div>
                  <div>
                    <p className="text-muted">Updated</p>
                    <p className="font-semibold">{syncData.counts.updated}</p>
                  </div>
                  <div>
                    <p className="text-muted">Unchanged</p>
                    <p className="font-semibold">{syncData.counts.unchanged}</p>
                  </div>
                  <div>
                    <p className="text-muted">Failed</p>
                    <p className="font-semibold">{syncData.counts.failed}</p>
                  </div>
                </div>
                {manualRefresh.isError ? (
                  <p className="text-sm text-red-200">Refresh failed. Try again after the backend is ready.</p>
                ) : null}
              </div>
            ) : null}
          </Card>

          <Card>
            {dashboardData ? (
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">Week snapshot</p>
                  <span className="text-muted">{dashboardData.last_successful_sync_at_utc ? "Synced" : "Waiting"}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-muted">Week range</p>
                    <p className="font-semibold">{formatDateRangeLabel(dashboardData.week_start_date, dashboardData.week_end_date)}</p>
                  </div>
                  <div>
                    <p className="text-muted">Current target volume</p>
                    <p className="font-semibold">
                      {dashboardData.zones.reduce((total, zone) => total + zone.target_minutes, 0)} min
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-muted">Last synced</p>
                  <p className="font-semibold">
                    {dashboardData.last_successful_sync_at_utc
                      ? new Date(dashboardData.last_successful_sync_at_utc).toLocaleString()
                      : "No successful sync yet"}
                  </p>
                </div>
              </div>
            ) : null}
          </Card>
        </div>
      </SectionShell>
    </>
  );
}
