import { screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsPage } from "../SettingsPage";
import { renderWithQueryClient } from "../../test/render";

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/integrations/whoop/status")) {
          return Promise.reject(new TypeError("Failed to fetch"));
        }
        if (url.endsWith("/api/v1/athlete-profile")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "Unauthorized" }), {
              status: 401,
              headers: { "content-type": "application/json" }
            })
          );
        }
        if (url.endsWith("/api/v1/settings")) {
          return Promise.reject(new TypeError("Failed to fetch"));
        }
        if (url.endsWith("/api/v1/ai/status")) {
          return Promise.resolve(
            new Response(JSON.stringify({ detail: "Unauthorized" }), {
              status: 401,
              headers: { "content-type": "application/json" }
            })
          );
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("shows actionable offline and locked messages and disables profile editing", async () => {
    renderWithQueryClient(<SettingsPage />);

    expect(
      (await screen.findAllByText("Backend is offline. Start the API on port 8000, then retry.")).length
    ).toBeGreaterThan(0);
    expect(
      (await screen.findAllByText("API access is locked. Use the API token, then reload this page.")).length
    ).toBeGreaterThan(0);

    const saveButton = screen.getByRole("button", { name: "Save profile" });
    expect(saveButton).toBeDisabled();
    expect(screen.getByText("Profile editing is disabled until the API loads successfully.")).toBeInTheDocument();
  });
});
