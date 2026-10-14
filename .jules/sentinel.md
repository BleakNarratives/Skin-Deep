# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-09-05 - Unvalidated Image Provider URL Schemes (SSRF/LFI)
**Vulnerability:** Fetching image URLs returned by external API integrations with `requests.get()` without scheme validation allows potential Server-Side Request Forgery (SSRF) or Local File Inclusion (LFI) via non-HTTP schemes like `file://` or `gopher://`.
**Learning:** External API responses containing URLs should never be trusted blindly before making network requests.
**Prevention:** Validate URL schemes using `url.lower().startswith(("https://", "http://"))` prior to making HTTP client requests.

## 2026-09-04 - Unsanitized Exception Formatting in FastAPI Handlers
**Vulnerability:** Raw `sqlite3.Error` string interpolation in FastAPI `HTTPException` detail fields leaked internal server paths (`/home/jules/MikeySwarm/persona_runs.db`) and database driver details.
**Learning:** Formatting raw exception objects into API response payloads leaks backend directory layouts and internal error details to unauthenticated callers.
**Prevention:** Always catch database exceptions and return sanitized, generic error details (`detail="corpus read failed"`) while logging exception details internally.
