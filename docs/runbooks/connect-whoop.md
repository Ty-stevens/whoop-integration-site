# Connect WHOOP Runbook

Use the app's WHOOP connect flow from the private deployment URL.

## Preconditions

- `WHOOP_CLIENT_ID` and `WHOOP_CLIENT_SECRET` are set.
- `WHOOP_REDIRECT_URI` matches the deployed URL.
- The backend health check is passing.

## Steps

1. Open the app.
2. Go to the WHOOP connect action from the settings or onboarding flow.
3. Sign in to WHOOP.
4. Approve the requested scopes.
5. Return to the app and confirm the connection status is `connected`.

## Verify

```bash
curl -f http://localhost:8080/api/v1/integrations/whoop/status
```

The response should show a connected account and non-expired tokens.
