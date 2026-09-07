# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-03-31 - SQLite Connection Leakage & Uncommitted Transactions in API Handlers
**Vulnerability:** Direct calls to `arena_db.get_conn().execute(...)` in route handlers bypassed context management, leaking connection handles and leaving uncommitted transactions under load.
**Learning:** SQLite helper functions must always wrap database connections with `with get_conn() as conn:` to ensure automatic transaction commits and resource cleanup.
**Prevention:** Never expose raw `get_conn().execute(...)` calls to route handlers; enforce database operations through dedicated `arena_db` functions that manage connection context.
