# ADR 0001: Product Defaults

## Status

Accepted.

ADRs are append-only unless a later ADR explicitly supersedes them.

## Context

EnduraSync needs stable defaults before schema, API, and UI work begins. The app should be useful before WHOOP credentials, scheduled sync, or AI are connected.

## Decision

- Product name: EnduraSync.
- Initial backfill: last 180 days.
- Week model: ISO weeks, Monday start.
- Export v1: CSV only.
- Auto-sync default: off.
- Midweek goal edit default: apply next Monday; optional apply-now behavior can be added later.
- Access model: Tailscale-only first; optional basic auth only if exposed beyond the private network or shared beyond one trusted user.
- Visual direction: Garmin-like dark tactical dashboard, desktop-first, responsive enough for tablet/mobile.
- Initial Zone 2 target: 150 minutes per week.
- Training progression: build Zone 2 by 15 to 30 minutes per build week, deload every 4th week by 20% to 30%.
- Initial weekly structure: 3 cardio sessions and 2 strength sessions.
- AI default: disabled.
- AI provider preference later: local OpenClaw if reachable and OpenAI-compatible; ChatGPT/OpenAI-compatible fallback.
- AI behavior later: recommend goals and feedback for approval, never silently mutate goals.

## Consequences

The dashboard, goals, reports, and settings can be built without waiting for provider setup. AI-related code must stay optional and isolated from WHOOP tokens and raw provider payloads.

## Open Questions

- Exact OpenClaw base URL, auth method, and model names are unknown until the private server is inspected.

