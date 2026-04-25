import { cleanup, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { AppProviders } from "./providers";
import { renderWithQueryClient } from "../test/render";

describe("App auth recovery", () => {
  beforeEach(() => {
    window.localStorage.setItem("endurasync_api_token", "stale-token");
    window.history.pushState({}, "", "/dashboard");

    vi.stubGlobal(
      "fetch",
      vi.fn((url: string) => {
        if (url.endsWith("/api/v1/health")) {
          return Promise.resolve(
            Response.json({
              app: "EnduraSync",
              status: "ok",
              environment: "production",
              version: "0.1.0",
              database: true,
              api_auth_required: true
            })
          );
        }

        return Promise.resolve(
          new Response(JSON.stringify({ detail: "Unauthorized" }), {
            status: 401,
            headers: { "content-type": "application/json" }
          })
        );
      })
    );
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    window.localStorage.clear();
    window.history.pushState({}, "", "/");
  });

  it("returns to the unlock screen when a saved token is rejected", async () => {
    renderWithQueryClient(
      <AppProviders>
        <App />
      </AppProviders>
    );

    expect(await screen.findByText("Private Access")).toBeInTheDocument();
    expect(
      screen.getByText((_, element) =>
        element?.textContent ===
        "The saved API token was rejected. Enter the current API_AUTH_TOKEN and try again."
      )
    ).toBeInTheDocument();
    expect(window.localStorage.getItem("endurasync_api_token")).toBeNull();
  });

  it("does not unlock when a newly entered token is rejected", async () => {
    window.localStorage.clear();

    const user = userEvent.setup();
    renderWithQueryClient(
      <AppProviders>
        <App />
      </AppProviders>
    );

    expect(await screen.findByText("Private Access")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("API token"), "wrong-token");
    await user.click(screen.getByRole("button", { name: "Unlock" }));

    expect(await screen.findByText("Private Access")).toBeInTheDocument();
    expect(
      screen.getByText((_, element) =>
        element?.textContent ===
        "The saved API token was rejected. Enter the current API_AUTH_TOKEN and try again."
      )
    ).toBeInTheDocument();
    expect(window.localStorage.getItem("endurasync_api_token")).toBeNull();
  });

  it("does not ask for an API token when the health check is unreachable", async () => {
    window.localStorage.clear();
    vi.stubGlobal("fetch", vi.fn(() => Promise.reject(new Error("Network unavailable"))));

    renderWithQueryClient(
      <AppProviders>
        <App />
      </AppProviders>
    );

    expect(await screen.findByText("API Unavailable")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("API token")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
