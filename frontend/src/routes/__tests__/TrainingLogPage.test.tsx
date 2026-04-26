import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { renderWithQueryClient } from "../../test/render";
import { TrainingLogPage } from "../TrainingLogPage";

const recentWorkoutsResponse = {
  workouts: [
    {
      id: 1,
      local_start_date: "2026-04-13",
      start_time_utc: "2026-04-13T12:00:00Z",
      sport_name: "Weightlifting",
      score_state: "SCORED",
      classification: "strength",
      effective_classification: "strength",
      duration_seconds: 3600,
      strain: 7.5,
      average_hr: 120,
      max_hr: 160,
      zone1_seconds: 600,
      zone2_seconds: 900,
      zone3_seconds: 300,
      zone4_seconds: 0,
      zone5_seconds: 0,
      annotation: {
        manual_classification: "strength",
        manual_strength_split: "upper",
        tag: "gym",
        notes: "Bench day",
        updated_at_utc: "2026-04-13T13:00:00Z"
      }
    }
  ]
};

const strengthOverviewResponse = {
  range_start_date: "2026-04-13",
  range_end_date: "2026-04-13",
  strength_sessions: 1,
  strength_strain: 7.5,
  split_counts: [
    { split: "upper", count: 1 },
    { split: "lower", count: 0 },
    { split: "full", count: 0 },
    { split: "unknown", count: 0 },
    { split: "untagged", count: 0 }
  ],
  weekly_counts: [{ period_start_date: "2026-04-13", label: "Week of 2026-04-13", count: 1 }],
  monthly_counts: [{ period_start_date: "2026-04-01", label: "Apr 2026", count: 1 }],
  untagged_sessions: 0
};

describe("TrainingLogPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/workouts/recent?limit=50")) {
          return Promise.resolve(Response.json(recentWorkoutsResponse));
        }
        if (url.endsWith("/api/v1/workouts/strength-overview?limit=180")) {
          return Promise.resolve(Response.json(strengthOverviewResponse));
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders recent workout annotations and strength overview", async () => {
    renderWithQueryClient(<TrainingLogPage />);

    expect(await screen.findByText("Weightlifting")).toBeInTheDocument();
    expect(screen.getByText("Strength sessions")).toBeInTheDocument();
    expect(screen.getByText("Z1")).toBeInTheDocument();
    expect(screen.getByText("15 min")).toBeInTheDocument();
    expect(screen.getByDisplayValue("gym")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Bench day")).toBeInTheDocument();
  });
});
