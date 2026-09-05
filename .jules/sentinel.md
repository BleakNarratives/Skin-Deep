# Sentinel's Security Journal - Critical Learnings

This journal tracks critical security learnings, unique vulnerability patterns, and architectural constraints discovered within this codebase.

## 2026-08-26 - Storyboard UI DOM XSS via Unescaped innerHTML
**Vulnerability:** Dynamic episode, scene, and panel data from backend API was directly interpolated into HTML template literals assigned to `.innerHTML` without entity escaping.
**Learning:** While Python backend export endpoints used `html.escape()`, the static frontend client rendered API objects directly into DOM via template string literals.
**Prevention:** Always sanitize dynamic strings using an HTML entity escape function (`esc()`) before setting `.innerHTML` in static web interfaces.
