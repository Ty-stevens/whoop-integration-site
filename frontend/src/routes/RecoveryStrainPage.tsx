import { useQuery } from "@tanstack/react-query";

import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PageHeader } from "../components/ui/PageHeader";
import { SectionShell } from "../components/ui/SectionShell";
import { StatBlock } from "../components/ui/StatBlock";
import { apiFetch, type RecoveryStrainTrends, type TrendWeeklyPoint } from "../lib/api";
import { formatDateRangeLabel } from "../lib/dates";
import { nullableNumberLabel } from "../lib/format";

function metricLabel(value: number | null, precision = 0) {
  return value === null ? "-" : value.toFixed(precision);
}

function directionText(direction: string, delta: number | null) {
  if (direction === "insufficient" || delta === null) {
    return "More history needed";
  }
  if (direction === "flat") {
    return "Steady";
  }
  return `${direction === "up" ? "Up" : "Down"} ${Math.abs(delta).toFixed(1)}`;
}

function MiniTrend({
  points,
  metric,
  label
}: {
  points: TrendWeeklyPoint[];
  metric: "average_recovery_score" | "average_daily_strain";
  label: string;
}) {
  const values = points.map((point) => point[metric]).filter((value): value is number => value !== null);
  const max = Math.max(...values, 1);

  return (
    <Card>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="font-semibold">{label}</p>
        <p className="text-sm text-muted">{values.length} weeks</p>
      </div>
      <div className="flex h-36 items-end gap-2" aria-label={`${label} weekly chart`}>
        {points.map((point) => {
          const value = point[metric];
          const height = value === null ? 4 : Math.max((value / max) * 100, 8);
          return (
            <div key={point.week_start_date} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <div
                className="w-full rounded-sm bg-accent"
                style={{
                  height: `${height}%`,
                  opacity: value === null ? 0.25 : 0.85
                }}
                title={`${point.week_start_date}: ${value ?? "no data"}`}
              />
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-sm text-muted">
        {points[0]?.week_start_date && points[points.length - 1]?.week_end_date
          ? formatDateRangeLabel(points[0].week_start_date, points[points.length - 1].week_end_date)
          : "No dated history"}
      </p>
    </Card>
  );
}

export function RecoveryStrainPage() {
  const trendsQuery = useQuery({
    queryKey: ["recovery-strain", "trends"],
    queryFn: () => apiFetch<RecoveryStrainTrends>("/api/v1/recovery-strain/trends")
  });

  const latestWeek = trendsQuery.data?.weekly_series[trendsQuery.data.weekly_series.length - 1];

  return (
    <>
      <PageHeader title="Recovery And Strain" eyebrow="Trends">
        <div className="text-sm text-muted">
          {trendsQuery.data
            ? formatDateRangeLabel(trendsQuery.data.range_start_week, trendsQuery.data.range_end_week)
            : "Recent weekly history"}
        </div>
      </PageHeader>

      {trendsQuery.isLoading ? <LoadingState message="Loading recovery and strain trends" /> : null}
      {trendsQuery.isError ? <ErrorState message="Recovery and strain trends are unavailable right now." /> : null}

      {trendsQuery.data?.data_state === "empty" ? (
        <EmptyState
          title="No trend history yet"
          body="Connect WHOOP and run a sync to populate recovery, sleep, and workout trends."
        />
      ) : null}

      {trendsQuery.data ? (
        <>
          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <StatBlock
                label="Latest recovery"
                value={nullableNumberLabel(latestWeek?.average_recovery_score ?? null)}
                hint={latestWeek ? `${latestWeek.recovery_count} recovery records this week` : "No weekly record"}
              />
            </Card>
            <Card>
              <StatBlock
                label="Latest strain"
                value={metricLabel(latestWeek?.average_daily_strain ?? null, 1)}
                hint={latestWeek ? `${latestWeek.workout_count} workouts this week` : "No weekly record"}
              />
            </Card>
            <Card>
              <StatBlock
                label="Recovery per strain"
                value={metricLabel(latestWeek?.recovery_per_strain ?? null, 2)}
                hint="Simple ratio for context"
              />
            </Card>
          </div>

          <SectionShell title="Four-Week Window">
            <div className="grid gap-4 lg:grid-cols-2">
              {trendsQuery.data.comparison_cards.map((card) => (
                <Card key={card.metric}>
                  <p className="text-sm text-muted">{card.label}</p>
                  <div className="mt-2 flex items-baseline justify-between gap-4">
                    <p className="text-3xl font-semibold">{metricLabel(card.current_average, 1)}</p>
                    <p className="text-sm text-muted">{directionText(card.direction, card.delta)}</p>
                  </div>
                  <p className="mt-3 text-sm text-muted">
                    Previous window {metricLabel(card.previous_average, 1)} ·{" "}
                    {formatDateRangeLabel(card.current_window_start_date, card.current_window_end_date)}
                  </p>
                </Card>
              ))}
            </div>
          </SectionShell>

          <SectionShell title="Trend Lines">
            <div className="grid gap-4 lg:grid-cols-2">
              <MiniTrend
                points={trendsQuery.data.weekly_series}
                metric="average_recovery_score"
                label="Weekly average recovery"
              />
              <MiniTrend
                points={trendsQuery.data.weekly_series}
                metric="average_daily_strain"
                label="Weekly average strain"
              />
            </div>
          </SectionShell>

          <SectionShell title="Interpretation">
            <Card>
              <p className="text-lg font-semibold">{trendsQuery.data.interpretation_text}</p>
              <p className="mt-2 text-sm text-muted">
                This is a deterministic read of synced trends, not medical advice.
              </p>
            </Card>
          </SectionShell>
        </>
      ) : null}
    </>
  );
}
