# ADR 0003: Week And Time Model

## Status

Accepted.

ADRs are append-only unless a later ADR explicitly supersedes them.

## Context

Training progress, reports, and exports must agree on week and date boundaries.

## Decision

- ISO weeks with Monday start are the only week definition.
- UTC timestamps are stored for canonical event times.
- Local date buckets are derived during import and stored for workouts, sleeps, and recoveries.
- Durations are stored in seconds and formatted as minutes only at API or UI boundaries.
- Reports and CSV exports use the same backend dataset builders.

## Consequences

All downstream metrics can group by stable stored date buckets. Sunday/Monday and month-boundary behavior must be covered by tests when import transformers are implemented.

