# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-03-31 - CSV Formula Injection in Export Endpoints
**Vulnerability:** Unsanitized user inputs in CSV export data starting with formula trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) allowed CSV formula injection (DDE/formula execution when opened in Excel or Google Sheets).
**Learning:** CSV serialization via standard `csv.DictWriter` handles structural delimiter quoting, but does not escape leading formula trigger characters within cell values.
**Prevention:** Always sanitize cell strings before CSV serialization by prepending a single quote `'` to any cell starting with `=`, `+`, `-`, `@`, `\t`, or `\r`.
