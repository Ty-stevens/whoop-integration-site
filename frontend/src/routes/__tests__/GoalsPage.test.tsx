import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { GoalsPage } from "../GoalsPage";
import { renderWithQueryClient } from "../../test/render";

const goalProfile = {
  id: 1,
  effective_from_date: "2026-04-13",
  effective_to_date: null,
  zone1_target_minutes: 30,
  zone2_target_minutes: 150,
  zone3_target_minutes: 20,
  zone4_target_minutes: 10,
  zone5_target_minutes: 0,
  cardio_sessions_target: 3,
  strength_sessions_target: 2,
  created_reason: null,
  created_at_utc: "2026-04-13T00:00:00Z"
};

describe("GoalsPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string, init?: RequestInit) => {
        if (url.endsWith("/api/v1/goals/active")) {
          return Promise.resolve(Response.json({ profile: goalProfile, message: "Active goal profile found." }));
        }
        if (url.endsWith("/api/v1/goals/history")) {
          return Promise.resolve(Response.json({ profiles: [goalProfile] }));
        }
        if (url.endsWith("/api/v1/goals/") && init?.method === "POST") {
          return Promise.resolve(Response.json({ ...goalProfile, id: 2, effective_from_date: "2026-04-20" }));
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders active goals and can submit the edit form", async () => {
    renderWithQueryClient(<GoalsPage />);

    expect(await screen.findByText("Zone 2 target")).toBeInTheDocument();
    expect(screen.getAllByText("150 min").length).toBeGreaterThan(0);

    await userEvent.click(screen.getByRole("button", { name: /save goal profile/i }));

    expect(await screen.findByText(/current/i)).toBeInTheDocument();
  });
});
