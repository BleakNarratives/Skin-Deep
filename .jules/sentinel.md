# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-03-31 - SQLite Connection Scoping & Exception Masking in REST Routes
**Vulnerability:** Raw exception interpolation in API response detail strings leaked database internal paths/schema details, and un-scoped SQLite connection handle instantiation leaked uncommitted transactions/handles in WAL mode.
**Learning:** `get_conn().execute(...)` called outside `with` context manager leaves connections open and uncommitted. Interpolating `{e}` into `HTTPException(detail=...)` exposes internal stack/database details to API clients.
**Prevention:** Always wrap connection calls in `with arena_db.get_conn() as conn:` context managers and return sanitized generic error messages in public endpoint exception handlers.
