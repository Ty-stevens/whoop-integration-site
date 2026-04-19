import { FormEvent, useState } from "react";
import { RouterProvider } from "react-router-dom";

import { Button } from "../components/ui/Button";
import { hasApiToken, setApiToken } from "../lib/api";
import { router } from "./router";

export function App() {
  const [tokenInput, setTokenInput] = useState("");
  const [unlocked, setUnlocked] = useState(hasApiToken());

  function unlock(event: FormEvent) {
    event.preventDefault();
    if (!tokenInput.trim()) {
      return;
    }
    setApiToken(tokenInput);
    setUnlocked(true);
  }

  if (!unlocked) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-5 text-primary">
        <div className="w-full max-w-md rounded-lg border border-line bg-surface p-6">
          <h1 className="text-xl font-semibold">Private Access</h1>
          <p className="mt-2 text-sm text-muted">
            Enter your API access token to unlock the dashboard.
          </p>
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
