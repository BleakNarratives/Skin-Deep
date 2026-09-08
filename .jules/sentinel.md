# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-03-30 - Database Exception Detail Leakage in FastAPI Endpoints
**Vulnerability:** SQLite exception strings (`str(e)`) were directly returned in `HTTPException` details in `arena_api.py`.
**Learning:** Returning raw exception messages to HTTP clients exposes internal database structure, query formatting, and server filesystem paths during database failures.
**Prevention:** Catch database exceptions and return generic, sanitized error detail messages (`"corpus read failed"`) in API responses.
