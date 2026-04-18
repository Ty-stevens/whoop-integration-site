import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SixMonthReportPage } from "../SixMonthReportPage";
import { renderWithQueryClient } from "../../test/render";

const reportResponse = {
  range_start_date: "2025-11-01",
  range_end_date: "2026-04-30",
  month_count: 6,
  monthly_summaries: [
    {
      month_start_date: "2026-04-01",
      month_end_date: "2026-04-30",
      month_label: "Apr 2026",
      workout_count: 5,
      sleep_count: 5,
      recovery_count: 5,
      training_seconds: 18000,
      zone1_minutes: 30,
      zone2_minutes: 180,
      zone3_minutes: 40,
      zone4_minutes: 20,
      zone5_minutes: 10,
      cardio_count: 3,
      strength_count: 2,
      other_count: 0,
      unknown_count: 0,
      average_recovery_score: 72,
      average_daily_strain: 11.4
    }
  ],
  consistency_summary: {
    weeks_in_range: 27,
    active_weeks: 4,
    weeks_with_workouts: 4,
    weeks_with_sleeps: 4,
    weeks_with_recoveries: 4,
    training_week_coverage_percent: 14.81,
    sleep_week_coverage_percent: 14.81,
    recovery_week_coverage_percent: 14.81,
    summary_text: "Training shows up regularly, but the window still has a few quiet weeks."
  }
};

describe("SixMonthReportPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/reports/six-month")) {
          return Promise.resolve(Response.json(reportResponse));
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the report summary and CSV action", async () => {
    renderWithQueryClient(<SixMonthReportPage />);

    expect(await screen.findByText("Training volume")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /export csv/i })).toBeInTheDocument();
    expect(screen.getByText("Apr 2026")).toBeInTheDocument();
  });
});
