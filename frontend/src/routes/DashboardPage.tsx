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

function formatPercent(value: number | null) {
  return value === null ? "—" : `${Math.round(value)}%`;
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

function zoneStatusText(zone: CurrentWeekDashboard["zones"][number]) {
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

  const weekLabel = dashboardQuery.data
    ? formatDateRangeLabel(dashboardQuery.data.week_start_date, dashboardQuery.data.week_end_date)
    : "Current ISO week";

  return (
    <>
      <PageHeader title="Current Week" eyebrow="Dashboard">
        <div className="text-sm text-muted">{weekLabel}</div>
      </PageHeader>

      {dashboardQuery.isLoading ? <LoadingState message="Loading current week metrics" /> : null}
      {dashboardQuery.isError ? <ErrorState message="Current week metrics are unavailable right now." /> : null}
      {syncStatusQuery.isLoading ? <LoadingState message="Loading sync status" /> : null}
      {syncStatusQuery.isError ? <ErrorState message="Sync status is unavailable right now." /> : null}

      {dashboardQuery.data ? (
        <>
          <div className="grid gap-4 lg:grid-cols-4">
            <Card className="lg:col-span-2">
              <StatBlock
                label="Weekly training"
                value={formatSeconds(dashboardQuery.data.total_training_seconds)}
                hint={`Week start ${formatLongDate(dashboardQuery.data.week_start_date)}`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Cardio sessions"
                value={`${dashboardQuery.data.cardio_sessions.completed} / ${dashboardQuery.data.cardio_sessions.target}`}
                hint={`${dashboardQuery.data.cardio_sessions.remaining} remaining`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Strength sessions"
                value={`${dashboardQuery.data.strength_sessions.completed} / ${dashboardQuery.data.strength_sessions.target}`}
                hint={`${dashboardQuery.data.strength_sessions.remaining} remaining`}
              />
            </Card>
          </div>

          <SectionShell title="HR Zone Progress">
            <div className="grid gap-4 lg:grid-cols-5">
              {dashboardQuery.data.zones.map((zone) => (
                <Card key={zone.zone}>
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <p className="font-semibold">{zoneLabels[`zone${zone.zone}` as keyof typeof zoneLabels]}</p>
                    <span className="text-sm text-muted">{formatPercent(zone.percent_complete)}</span>
                  </div>
                  <ProgressBar value={zone.percent_complete ?? 0} color={zoneColors[`zone${zone.zone}` as keyof typeof zoneColors]} />
                  <p className="mt-3 text-sm text-muted">
                    {minutesLabel(zone.actual_minutes)} of {minutesLabel(zone.target_minutes)}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    {zoneStatusText(zone)}
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
                  value={dashboardQuery.data.average_recovery_score === null ? "—" : Math.round(dashboardQuery.data.average_recovery_score).toString()}
                  hint="Backend-derived from synced recovery records"
                />
              </Card>
              <Card>
                <StatBlock
                  label="Average daily strain"
                  value={dashboardQuery.data.average_daily_strain === null ? "—" : Math.round(dashboardQuery.data.average_daily_strain).toString()}
                  hint="Backend-derived from synced workout records"
                />
              </Card>
              <Card>
                <StatBlock
                  label="Goal profile"
                  value={dashboardQuery.data.has_goal_profile ? `#${dashboardQuery.data.goal_profile_id}` : "Unset"}
                  hint={dashboardQuery.data.has_goal_profile ? "Active for this week" : "No active goal profile"}
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
            {syncStatusQuery.data ? (
              <div className="space-y-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold">{syncBadge(syncStatusQuery.data.status)}</p>
                    <p className="mt-1 text-sm text-muted">{syncStatusQuery.data.message}</p>
                  </div>
                  <Button disabled={manualRefresh.isPending} onClick={() => manualRefresh.mutate()}>
                    {manualRefresh.isPending ? "Refreshing" : "Refresh now"}
                  </Button>
                </div>
                <div className="grid gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <p className="text-muted">Auto sync</p>
                    <p className="font-semibold">
                      {syncStatusQuery.data.auto_sync_enabled ? syncStatusQuery.data.auto_sync_frequency : "Disabled"}
                    </p>
                  </div>
                  <div>
                    <p className="text-muted">Last success</p>
                    <p className="font-semibold">
                      {syncStatusQuery.data.last_success_at_utc
                        ? formatLongDate(syncStatusQuery.data.last_success_at_utc.slice(0, 10))
                        : "None yet"}
                    </p>
                  </div>
                </div>
                <div className="grid gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <p className="text-muted">Inserted</p>
                    <p className="font-semibold">{syncStatusQuery.data.counts.inserted}</p>
                  </div>
                  <div>
                    <p className="text-muted">Updated</p>
                    <p className="font-semibold">{syncStatusQuery.data.counts.updated}</p>
                  </div>
                  <div>
                    <p className="text-muted">Unchanged</p>
                    <p className="font-semibold">{syncStatusQuery.data.counts.unchanged}</p>
                  </div>
                  <div>
                    <p className="text-muted">Failed</p>
                    <p className="font-semibold">{syncStatusQuery.data.counts.failed}</p>
                  </div>
                </div>
                {manualRefresh.isError ? (
                  <p className="text-sm text-red-200">Refresh failed. Try again after the backend is ready.</p>
                ) : null}
              </div>
            ) : null}
          </Card>

          <Card>
            {dashboardQuery.data ? (
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold">Week snapshot</p>
                  <span className="text-muted">{dashboardQuery.data.last_successful_sync_at_utc ? "Synced" : "Waiting"}</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-muted">Week range</p>
                    <p className="font-semibold">{formatDateRangeLabel(dashboardQuery.data.week_start_date, dashboardQuery.data.week_end_date)}</p>
                  </div>
                  <div>
                    <p className="text-muted">Current target volume</p>
                    <p className="font-semibold">
                      {dashboardQuery.data.zones.reduce((total, zone) => total + zone.target_minutes, 0)} min
                    </p>
                  </div>
                </div>
                <div>
                  <p className="text-muted">Last synced</p>
                  <p className="font-semibold">
                    {dashboardQuery.data.last_successful_sync_at_utc
                      ? new Date(dashboardQuery.data.last_successful_sync_at_utc).toLocaleString()
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
