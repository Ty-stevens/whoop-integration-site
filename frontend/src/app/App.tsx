import { FormEvent, useEffect, useState } from "react";
import { RouterProvider } from "react-router-dom";

import { Button } from "../components/ui/Button";
import {
  API_AUTH_INVALID_EVENT,
  apiUrl,
  apiFetch,
  clearApiToken,
  hasApiToken,
  setApiToken,
  type HealthResponse
} from "../lib/api";
import { router } from "./router";

export function App() {
  const [tokenInput, setTokenInput] = useState("");
  const [authRequired, setAuthRequired] = useState<boolean | null>(null);
  const [healthCheckFailed, setHealthCheckFailed] = useState(false);
  const [unlocked, setUnlocked] = useState(hasApiToken());
  const [tokenRejected, setTokenRejected] = useState(false);
  const [unlocking, setUnlocking] = useState(false);
  const [authCheckAttempt, setAuthCheckAttempt] = useState(0);

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
        setHealthCheckFailed(false);
        if (!health.api_auth_required) {
          setUnlocked(true);
          return;
        }
        if (!hasApiToken()) {
          setUnlocked(false);
          return;
        }
        try {
          await apiFetch("/api/v1/settings");
          if (!cancelled) {
            setUnlocked(true);
          }
        } catch {
          if (!cancelled) {
            setUnlocked(false);
          }
        }
      } catch {
        if (cancelled) {
          return;
        }
        setHealthCheckFailed(true);
        setAuthRequired(null);
        setUnlocked(false);
      }
    }

    void detectAuthRequirement();

    return () => {
      cancelled = true;
    };
  }, [authCheckAttempt]);

  useEffect(() => {
    function handleInvalidToken() {
      clearApiToken();
      setAuthRequired(true);
      setTokenRejected(true);
      setUnlocked(false);
    }

    window.addEventListener(API_AUTH_INVALID_EVENT, handleInvalidToken);
    return () => {
      window.removeEventListener(API_AUTH_INVALID_EVENT, handleInvalidToken);
    };
  }, []);

  async function unlock(event: FormEvent) {
    event.preventDefault();
    if (!tokenInput.trim()) {
      return;
    }
    setUnlocking(true);
    setTokenRejected(false);
    setApiToken(tokenInput);

    try {
      await apiFetch("/api/v1/settings");
      setUnlocked(true);
    } catch {
      clearApiToken();
      setUnlocked(false);
      setTokenRejected(true);
    } finally {
      setUnlocking(false);
    }
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

  if (healthCheckFailed) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-5 text-primary">
        <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold">API Unavailable</h1>
          <p className="mt-2 text-sm text-muted">
            The site could not reach the backend health check. API tokens are only needed when the
            backend explicitly enables private access.
          </p>
          {tokenRejected ? (
            <p className="mt-2 text-sm text-red-200">
              The saved API token was rejected. The app cleared it so this browser will check access
              normally next time.
            </p>
          ) : null}
          <Button
            className="mt-4"
            type="button"
            onClick={() => {
              setHealthCheckFailed(false);
              setTokenRejected(false);
              setAuthCheckAttempt((attempt) => attempt + 1);
            }}
          >
            Retry
          </Button>
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
          {tokenRejected ? (
            <p className="mt-2 text-sm text-red-200">
              The saved API token was rejected. Enter the current <code>API_AUTH_TOKEN</code> and try again.
            </p>
          ) : null}
          <form className="mt-4 space-y-3" onSubmit={unlock}>
            <input
              className="w-full rounded-md border border-line bg-raised px-3 py-2 text-primary"
              placeholder="API token"
              value={tokenInput}
              disabled={unlocking}
              onChange={(event) => setTokenInput(event.target.value)}
              autoComplete="off"
            />
            <Button type="submit" disabled={unlocking}>
              {unlocking ? "Checking token..." : "Unlock"}
            </Button>
          </form>
        </div>
      </div>
    );
  }

  return <RouterProvider router={router} />;
}
