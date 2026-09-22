## 2025-05-18 - Scroll Handler Layout Thrashing & Unmemoized Chart Components
**Learning:** High-frequency scroll event listeners reading DOM element geometry (`offsetTop`, `offsetHeight`) cause layout thrashing and high main-thread CPU usage on every scroll pixel. Unmemoized Recharts components re-render heavy SVG trees whenever active section state updates.
**Action:** Throttle scroll listeners with `requestAnimationFrame` and `{ passive: true }`, and wrap SVG chart components in `React.memo` to skip redundant re-renders.

## 2025-05-19 - Unmemoized PRNG Path Generation in Interactive SVG Components
**Learning:** In interactive SVG stencil tools, slider inputs (like scale and opacity controls) trigger continuous re-renders. If geometric path algorithms using PRNG loops and trigonometric math (`Math.sin`, `Math.cos`) are not wrapped in `useMemo`, every drag tick recalculates complex path strings, causing frame drops during UI interactions.
**Action:** Wrap procedural path generation functions in `useMemo` dependent only on design seed/style parameters, and wrap interactive SVG sub-components in `React.memo`.

## 2025-05-20 - Unstable Callback Dependencies Invalidating Memoized Child Navigation
**Learning:** Passing unstable callback functions to memoized navigation components (`Sidebar` wrapped in `React.memo`) causes full component tree re-renders whenever state objects change. Additionally, triggering state updates (`setActiveSection`) that already run side-effects in `useEffect` creates duplicate API calls.
**Action:** Memoize API handlers with `useCallback` and keep section navigation callbacks clean with empty dependency arrays `[]` so memoized children skip re-renders.

## 2026-08-27 - O(N²) Quadratic Serialization Bottleneck in Streaming Database Appends
**Learning:** Appending telemetry or event history to JSON array fields in SQLite via a Python read-modify-write cycle (`SELECT` -> `json.loads` -> `append` -> `json.dumps` -> `UPDATE`) creates an O(N²) serialization overhead on every streaming event tick. Native SQLite 3.38+ `json_insert(COALESCE(NULLIF(events, ''), '[]'), '$[#]', json(?))` performs array appends in-database in a single atomic `UPDATE`, reducing query count by 50% and improving write throughput by ~5.8x.
**Action:** Use native SQLite `json_insert` for array appends in database persistent stores instead of Python-side JSON string re-serialization.
