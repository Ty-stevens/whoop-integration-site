import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DashboardPage } from "../DashboardPage";
import { renderWithQueryClient } from "../../test/render";

const dashboardResponse = {
  week_start_date: "2026-04-13",
  week_end_date: "2026-04-19",
  has_goal_profile: true,
  goal_profile_id: 1,
  last_successful_sync_at_utc: "2026-04-17T12:00:00Z",
  zones: [
    {
      zone: 1,
      actual_seconds: 1200,
      actual_minutes: 20,
      target_minutes: 30,
      percent_complete: 66.67,
      remaining_minutes: 10,
      exceeded: false
    },
    {
      zone: 2,
      actual_seconds: 10800,
      actual_minutes: 180,
      target_minutes: 150,
      percent_complete: 120,
      remaining_minutes: 0,
      exceeded: true
    }
  ],
  cardio_sessions: { completed: 2, target: 3, remaining: 1, percent_complete: 66.67 },
  strength_sessions: { completed: 1, target: 2, remaining: 1, percent_complete: 50 },
  total_training_seconds: 7200,
  average_recovery_score: 72,
  average_daily_strain: 11.2
};

const syncStatusResponse = {
  status: "success",
  auto_sync_enabled: false,
  auto_sync_frequency: "daily",
  last_success_at_utc: "2026-04-17T12:00:00Z",
  latest_run: null,
  outcomes: [],
  counts: { inserted: 1, updated: 0, unchanged: 2, failed: 0 },
  message: "Sync completed successfully."
};

describe("DashboardPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/dashboard/current-week")) {
          return Promise.resolve(Response.json(dashboardResponse));
        }
        if (url.endsWith("/api/v1/sync/status")) {
          return Promise.resolve(Response.json(syncStatusResponse));
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders populated weekly metrics and sync state", async () => {
    renderWithQueryClient(<DashboardPage />);

    expect(await screen.findByText("Weekly training")).toBeInTheDocument();
    expect(screen.getByText("2 hr")).toBeInTheDocument();
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
    expect(screen.getByText("30 min over target")).toBeInTheDocument();
    expect(screen.getByText("Sync completed successfully.")).toBeInTheDocument();
  });

  it("shows actual HR zone minutes when benchmark targets are unset", async () => {
    vi.mocked(fetch).mockImplementation((input: Parameters<typeof fetch>[0]) => {
      const url = input.toString();
      if (url.endsWith("/api/v1/dashboard/current-week")) {
        return Promise.resolve(
          Response.json({
            ...dashboardResponse,
            has_goal_profile: false,
            goal_profile_id: null,
            zones: [
              {
                zone: 1,
                actual_seconds: 1800,
                actual_minutes: 30,
                target_minutes: 0,
                percent_complete: null,
                remaining_minutes: 0,
                exceeded: true
              },
              {
                zone: 2,
                actual_seconds: 3600,
                actual_minutes: 60,
                target_minutes: 0,
                percent_complete: null,
                remaining_minutes: 0,
                exceeded: true
              }
            ]
          })
        );
      }
      if (url.endsWith("/api/v1/sync/status")) {
        return Promise.resolve(Response.json(syncStatusResponse));
      }
      return Promise.reject(new Error(`Unexpected URL ${url}`));
    });

    renderWithQueryClient(<DashboardPage />);

    expect(await screen.findByText("30 min logged")).toBeInTheDocument();
    expect(screen.getByText("67% of HR zone time")).toBeInTheDocument();
  });
});
