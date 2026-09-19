## 2025-05-18 - Scroll Handler Layout Thrashing & Unmemoized Chart Components
**Learning:** High-frequency scroll event listeners reading DOM element geometry (`offsetTop`, `offsetHeight`) cause layout thrashing and high main-thread CPU usage on every scroll pixel. Unmemoized Recharts components re-render heavy SVG trees whenever active section state updates.
**Action:** Throttle scroll listeners with `requestAnimationFrame` and `{ passive: true }`, and wrap SVG chart components in `React.memo` to skip redundant re-renders.

## 2025-05-19 - Unmemoized PRNG Path Generation in Interactive SVG Components
**Learning:** In interactive SVG stencil tools, slider inputs (like scale and opacity controls) trigger continuous re-renders. If geometric path algorithms using PRNG loops and trigonometric math (`Math.sin`, `Math.cos`) are not wrapped in `useMemo`, every drag tick recalculates complex path strings, causing frame drops during UI interactions.
**Action:** Wrap procedural path generation functions in `useMemo` dependent only on design seed/style parameters, and wrap interactive SVG sub-components in `React.memo`.

## 2025-05-20 - Unstable Callback Dependencies Invalidating Memoized Child Navigation
**Learning:** Passing unstable callback functions to memoized navigation components (`Sidebar` wrapped in `React.memo`) causes full component tree re-renders whenever state objects change. Additionally, triggering state updates (`setActiveSection`) that already run side-effects in `useEffect` creates duplicate API calls.
**Action:** Memoize API handlers with `useCallback` and keep section navigation callbacks clean with empty dependency arrays `[]` so memoized children skip re-renders.

## 2026-02-04 - SQLite N+1 Connection & Query Overhead in Tree Aggregations
**Learning:** Nested helper calls that open and close separate connection context managers (`with _ro() as conn:`) in SQLite result in N+1 query patterns and significant connection management overhead when assembling hierarchical objects like `episode_tree`.
**Action:** Single-pass tree construction inside one connection context, using `IN (...)` batch queries for child entities (e.g. panels by scene IDs), reduces query count and connection churn by >3x.
