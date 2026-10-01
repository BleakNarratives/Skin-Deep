# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-10-01 - Absolute Server Home Path Exposure in Keyring and Health Status Endpoints
**Vulnerability:** `KeyPool.status()` and `/api/v1/storyboard/health` endpoints exposed unmasked `Path.home()` directory paths (`/home/jules/.concierge/vault`), leaking internal server filesystem layouts and system usernames to unauthenticated callers.
**Learning:** Returning unmasked `Path` objects in status payloads exposes server directory structure and internal user accounts.
**Prevention:** Always mask home directory paths using `_sanitize_path()` (replacing `Path.home()` with `~`) before including directory paths in public status or health responses.

## 2026-09-04 - Unsanitized Exception Formatting in FastAPI Handlers
**Vulnerability:** Raw `sqlite3.Error` string interpolation in FastAPI `HTTPException` detail fields leaked internal server paths (`/home/jules/MikeySwarm/persona_runs.db`) and database driver details.
**Learning:** Formatting raw exception objects into API response payloads leaks backend directory layouts and internal error details to unauthenticated callers.
**Prevention:** Always catch database exceptions and return sanitized, generic error details (`detail="corpus read failed"`) while logging exception details internally.
