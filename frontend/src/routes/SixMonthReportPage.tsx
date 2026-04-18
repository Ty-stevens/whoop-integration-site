import { useMutation, useQuery } from "@tanstack/react-query";

import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { ErrorState } from "../components/ui/ErrorState";
import { LoadingState } from "../components/ui/LoadingState";
import { PageHeader } from "../components/ui/PageHeader";
import { ProgressBar } from "../components/ui/ProgressBar";
import { SectionShell } from "../components/ui/SectionShell";
import { StatBlock } from "../components/ui/StatBlock";
import { apiFetch, type MonthlyTrainingSummary, type SixMonthReport } from "../lib/api";
import { formatDateRangeLabel } from "../lib/dates";
import { nullableNumberLabel, secondsToDurationLabel } from "../lib/format";
import { zoneColors, zoneLabels } from "../lib/zones";

function totalTrainingSeconds(months: MonthlyTrainingSummary[]) {
  return months.reduce((total, month) => total + month.training_seconds, 0);
}

function downloadCsv(csv: string, filename: string) {
  const blob = new globalThis.Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = globalThis.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  globalThis.URL.revokeObjectURL(url);
}

function MonthVolumeChart({ months }: { months: MonthlyTrainingSummary[] }) {
  const maxSeconds = Math.max(...months.map((month) => month.training_seconds), 1);
  return (
    <Card>
      <div className="mb-4 flex items-center justify-between gap-3">
        <p className="font-semibold">Monthly Training Volume</p>
        <p className="text-sm text-muted">{months.length} months</p>
      </div>
      <div className="flex h-40 items-end gap-3" aria-label="Monthly training volume chart">
        {months.map((month) => {
          const height = Math.max((month.training_seconds / maxSeconds) * 100, month.training_seconds ? 8 : 3);
          return (
            <div key={month.month_start_date} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <div
                className="w-full rounded-sm bg-signal"
                style={{ height: `${height}%`, opacity: month.training_seconds ? 0.9 : 0.25 }}
                title={`${month.month_label}: ${secondsToDurationLabel(month.training_seconds)}`}
              />
              <span className="truncate text-xs text-muted">{month.month_label.split(" ")[0]}</span>
            </div>
          );
        })}
      </div>
    </Card>
  );
}

function ZoneDistribution({ months }: { months: MonthlyTrainingSummary[] }) {
  const zoneMinutes = (month: MonthlyTrainingSummary, zone: number) => {
    if (zone === 1) return month.zone1_minutes;
    if (zone === 2) return month.zone2_minutes;
    if (zone === 3) return month.zone3_minutes;
    if (zone === 4) return month.zone4_minutes;
    return month.zone5_minutes;
  };
  const totals = [1, 2, 3, 4, 5].map((zone) => ({
    zone,
    minutes: months.reduce((total, month) => total + zoneMinutes(month, zone), 0)
  }));
  const max = Math.max(...totals.map((item) => item.minutes), 1);
  return (
    <Card>
      <p className="mb-4 font-semibold">Zone Distribution</p>
      <div className="space-y-4">
        {totals.map((item) => {
          const key = `zone${item.zone}` as keyof typeof zoneLabels;
          return (
            <div key={item.zone}>
              <div className="mb-2 flex justify-between gap-3 text-sm">
                <span>{zoneLabels[key]}</span>
                <span className="text-muted">{item.minutes} min</span>
              </div>
              <ProgressBar value={(item.minutes / max) * 100} color={zoneColors[key]} />
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export function SixMonthReportPage() {
  const reportQuery = useQuery({
    queryKey: ["reports", "six-month"],
    queryFn: () => apiFetch<SixMonthReport>("/api/v1/reports/six-month")
  });

  const exportCsv = useMutation({
    mutationFn: () => apiFetch<string>("/api/v1/reports/six-month/export.csv"),
    onSuccess: (csv) => {
      if (!reportQuery.data) {
        return;
      }
      downloadCsv(csv, `six-month-report-${reportQuery.data.range_start_date}_to_${reportQuery.data.range_end_date}.csv`);
    }
  });

  const report = reportQuery.data;
  const hasTraining = report ? totalTrainingSeconds(report.monthly_summaries) > 0 : false;

  return (
    <>
      <PageHeader title="6-Month Report" eyebrow="Long View">
        <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
          <span>
            {report ? formatDateRangeLabel(report.range_start_date, report.range_end_date) : "Six-month training window"}
          </span>
          <Button variant="secondary" disabled={!report || exportCsv.isPending} onClick={() => exportCsv.mutate()}>
            {exportCsv.isPending ? "Exporting" : "Export CSV"}
          </Button>
        </div>
      </PageHeader>

      {reportQuery.isLoading ? <LoadingState message="Loading six-month report" /> : null}
      {reportQuery.isError ? <ErrorState message="Six-month report is unavailable right now." /> : null}
      {exportCsv.isError ? <ErrorState message="CSV export failed. Retry after the backend is reachable." /> : null}

      {report && !hasTraining ? (
        <EmptyState
          title="No training volume in this window"
          body="The report is ready, but synced workouts have not landed in the current six-month range yet."
        />
      ) : null}

      {report ? (
        <>
          <div className="grid gap-4 lg:grid-cols-4">
            <Card className="lg:col-span-2">
              <StatBlock
                label="Training volume"
                value={secondsToDurationLabel(totalTrainingSeconds(report.monthly_summaries))}
                hint={`${report.consistency_summary.weeks_with_workouts} weeks with workouts`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Recovery coverage"
                value={nullableNumberLabel(report.consistency_summary.recovery_week_coverage_percent, "%")}
                hint={`${report.consistency_summary.weeks_with_recoveries} recovery weeks`}
              />
            </Card>
            <Card>
              <StatBlock
                label="Training coverage"
                value={nullableNumberLabel(report.consistency_summary.training_week_coverage_percent, "%")}
                hint={`${report.consistency_summary.active_weeks} active weeks`}
              />
            </Card>
          </div>

          <SectionShell title="Monthly Summary">
            <div className="grid gap-4 lg:grid-cols-2">
              <MonthVolumeChart months={report.monthly_summaries} />
              <ZoneDistribution months={report.monthly_summaries} />
            </div>
          </SectionShell>

          <SectionShell title="Month Details">
            <Card>
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-sm">
                  <thead className="text-muted">
                    <tr>
                      <th className="py-2 pr-4 font-medium">Month</th>
                      <th className="py-2 pr-4 font-medium">Volume</th>
                      <th className="py-2 pr-4 font-medium">Cardio</th>
                      <th className="py-2 pr-4 font-medium">Strength</th>
                      <th className="py-2 pr-4 font-medium">Recovery</th>
                      <th className="py-2 pr-4 font-medium">Strain</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.monthly_summaries.map((month) => (
                      <tr key={month.month_start_date}>
                        <td className="py-2 pr-4 font-semibold">{month.month_label}</td>
                        <td className="py-2 pr-4">{secondsToDurationLabel(month.training_seconds)}</td>
                        <td className="py-2 pr-4">{month.cardio_count}</td>
                        <td className="py-2 pr-4">{month.strength_count}</td>
                        <td className="py-2 pr-4">{nullableNumberLabel(month.average_recovery_score)}</td>
                        <td className="py-2 pr-4">{month.average_daily_strain?.toFixed(1) ?? "-"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </SectionShell>

          <SectionShell title="Consistency">
            <Card>
              <p className="text-lg font-semibold">{report.consistency_summary.summary_text}</p>
              <p className="mt-2 text-sm text-muted">
                {report.consistency_summary.weeks_in_range} weeks checked across training, sleep, and recovery records.
              </p>
            </Card>
          </SectionShell>
        </>
      ) : null}
    </>
  );
}
