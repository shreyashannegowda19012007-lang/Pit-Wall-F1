# Formula 1 Live Telemetry & Provider Access Guardrails

## 1. Zero Silent Fallback to Simulated Telemetry in Live Mode
- Production `LIVE` modes must connect exclusively to verified, authorized external provider feeds.
- When an external provider is unreachable, rate-limited, or locked behind an authentication barrier (`HTTP 401: Live F1 session in progress`), the system must display verified status badges (`AUTHENTICATION REQUIRED`, `[UNAVAILABLE - AUTH REQUIRED]`).
- Simulated test streams must be isolated under explicit user-selected toggles (`TEST STREAM`) and labeled strictly with `provenance: "TEST_STREAM"` and `data_classification: "HYPOTHETICAL"`.
- A failed live request must never silently produce flatline or manufactured car telemetry.

## 2. Active Session Guard for FastF1
- Never invoke `fastf1.get_session(...).load()` on active, ongoing, or current sessions (< 3.5 hours from session start time).
- FastF1 relies on post-session static archive dumps from Ergast. Calling `load()` during a live session will trigger sequential HTTP network timeouts.
- For driver rosters and entry lists during live/current sessions, resolve from real-time API or historical season standings (e.g., Jolpica).

## 3. Session Identity & Context Synchronization
- Never infer session identity from hardcoded session IDs or prior practice session keys.
- Synchronize global navigation context (`Season`, `Round`, `Session Type`) and telemetry panels bidirectionally so all indicators and charts reference the same verified session.
