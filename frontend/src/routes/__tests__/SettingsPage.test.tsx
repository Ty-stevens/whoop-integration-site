import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { SettingsPage } from "../SettingsPage";
import { browserNavigation } from "../../lib/api";
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

  it("starts WHOOP OAuth with a JSON authorization URL and then navigates", async () => {
    const assign = vi.spyOn(browserNavigation, "assign").mockImplementation(() => undefined);
    const user = userEvent.setup();
    const authorizationUrl =
      "https://api.prod.whoop.com/oauth/oauth2/auth?client_id=client-id&state=state";

    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/integrations/whoop/status")) {
          return Promise.resolve(
            Response.json({
              status: "disconnected",
              credentials_configured: true,
              connected_at_utc: null,
              last_token_refresh_at_utc: null,
              token_expires_at_utc: null,
              granted_scopes: null,
              message: "WHOOP credentials are configured, but no connection is stored."
            })
          );
        }
        if (url.endsWith("/api/v1/integrations/whoop/connect/start")) {
          return Promise.resolve(Response.json({ authorization_url: authorizationUrl }));
        }
        if (url.endsWith("/api/v1/athlete-profile")) {
          return Promise.resolve(
            Response.json({
              display_name: null,
              gender: null,
              date_of_birth: null,
              age_years: null,
              height_cm: null,
              weight_kg: null,
              training_focus: null,
              experience_level: null,
              notes_for_ai: null,
              ai_context_allowed: true
            })
          );
        }
        if (url.endsWith("/api/v1/settings")) {
          return Promise.resolve(
            Response.json({
              auto_sync_enabled: false,
              auto_sync_frequency: "daily",
              preferred_export_format: "csv",
              preferred_units: "metric"
            })
          );
        }
        if (url.endsWith("/api/v1/ai/status")) {
          return Promise.resolve(
            Response.json({
              status: "disabled",
              provider: "disabled",
              enabled: false,
              model: null,
              message: "AI is disabled."
            })
          );
        }
        return Promise.reject(new Error(`Unexpected URL ${url}`));
      })
    );

    renderWithQueryClient(<SettingsPage />);

    await user.click(await screen.findByRole("button", { name: "Connect WHOOP" }));

    await waitFor(() => expect(assign).toHaveBeenCalledWith(authorizationUrl));
  });
});
