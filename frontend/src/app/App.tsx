import { FormEvent, useEffect, useState } from "react";
import { RouterProvider } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { apiUrl, hasApiToken, setApiToken, type HealthResponse } from "../lib/api";
import { router } from "./router";

export function App() {
  const [tokenInput, setTokenInput] = useState("");
  const [authRequired, setAuthRequired] = useState<boolean | null>(null);
  const [healthCheckFailed, setHealthCheckFailed] = useState(false);
  const [unlocked, setUnlocked] = useState(hasApiToken());

  useEffect(() => {
    let cancelled = false;

    async function detectAuthRequirement() {
      try {
        const response = await fetch(apiUrl("/api/v1/health"));
        if (!response.ok) {
          throw new Error(`Health request failed with ${response.status}`);
        }
        const health = (await response.json()) as HealthResponse;
        if (cancelled) {
          return;
        }
        setAuthRequired(health.api_auth_required);
        setUnlocked(!health.api_auth_required || hasApiToken());
      } catch {
        if (cancelled) {
          return;
        }
        setHealthCheckFailed(true);
        setUnlocked(hasApiToken());
      }
    }

    void detectAuthRequirement();

    return () => {
      cancelled = true;
    };
  }, []);

  function unlock(event: FormEvent) {
    event.preventDefault();
    if (!tokenInput.trim()) {
      return;
    }
    setApiToken(tokenInput);
    setUnlocked(true);
  }

  if (authRequired === null && !healthCheckFailed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-5 text-primary">
        <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold">Checking Access</h1>
          <p className="mt-2 text-sm text-muted">
            Contacting the API to see whether this deployment is locked.
          </p>
        </div>
      </div>
    );
  }

  if (!unlocked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-5 text-primary">
        <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold">Private Access</h1>
          <p className="mt-2 text-sm text-muted">
            Enter the server's <code>API_AUTH_TOKEN</code> to unlock the dashboard.
          </p>
          <p className="mt-2 text-sm text-muted">
            If you are running locally with the default placeholder config, you should not be
            prompted for a token. This screen usually means the deployment is intentionally locked.
          </p>
          {healthCheckFailed ? (
            <p className="mt-2 text-sm text-muted">
              The app could not confirm the backend auth mode, so it is falling back to manual
              unlock.
            </p>
          ) : null}
          <form className="mt-4 space-y-3" onSubmit={unlock}>
            <input
              className="w-full rounded-md border border-line bg-raised px-3 py-2 text-primary"
              placeholder="API token"
              value={tokenInput}
              onChange={(event) => setTokenInput(event.target.value)}
              autoComplete="off"
            />
            <Button type="submit">Unlock</Button>
          </form>
        </div>
      </div>
    );
  }

  return <RouterProvider router={router} />;
}
