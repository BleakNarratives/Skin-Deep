# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-09-04 - Unsanitized Exception Formatting in FastAPI Handlers
**Vulnerability:** Raw `sqlite3.Error` string interpolation in FastAPI `HTTPException` detail fields leaked internal server paths (`/home/jules/MikeySwarm/persona_runs.db`) and database driver details.
**Learning:** Formatting raw exception objects into API response payloads leaks backend directory layouts and internal error details to unauthenticated callers.
**Prevention:** Always catch database exceptions and return sanitized, generic error details (`detail="corpus read failed"`) while logging exception details internally.
