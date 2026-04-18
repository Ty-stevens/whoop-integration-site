# AI Integration Handoff

This document records the live server facts needed before AI provider work starts.

## Record here

- Server hostname or friendly name
- Private URL or Tailscale address
- Deployment path
- Container names or service names
- Backup path
- Reverse proxy details
- Whether outbound internet is allowed from the app container
- Where `AI_ENABLED`, `AI_PROVIDER`, `AI_BASE_URL`, `AI_MODEL`, and `AI_API_KEY` live
- Who owns the final manual hookup

## Current stance

- AI is disabled by default.
- The app should not depend on any AI secret being present in the frontend.
- Secrets stay on the server and out of the repository.

## OpenClaw note

If OpenClaw exists on the server, record its process name, base URL, port, auth method, and model names here. If it does not exist, say that plainly instead of assuming it is available.

## Handoff rule

Do not start AI integration work until the server layout and the provider endpoint are confirmed in writing.
