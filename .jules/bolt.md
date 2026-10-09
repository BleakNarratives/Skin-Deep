## 2025-05-18 - Scroll Handler Layout Thrashing & Unmemoized Chart Components
**Learning:** High-frequency scroll event listeners reading DOM element geometry (`offsetTop`, `offsetHeight`) cause layout thrashing and high main-thread CPU usage on every scroll pixel. Unmemoized Recharts components re-render heavy SVG trees whenever active section state updates.
**Action:** Throttle scroll listeners with `requestAnimationFrame` and `{ passive: true }`, and wrap SVG chart components in `React.memo` to skip redundant re-renders.

## 2025-05-19 - Unmemoized PRNG Path Generation in Interactive SVG Components
**Learning:** In interactive SVG stencil tools, slider inputs (like scale and opacity controls) trigger continuous re-renders. If geometric path algorithms using PRNG loops and trigonometric math (`Math.sin`, `Math.cos`) are not wrapped in `useMemo`, every drag tick recalculates complex path strings, causing frame drops during UI interactions.
**Action:** Wrap procedural path generation functions in `useMemo` dependent only on design seed/style parameters, and wrap interactive SVG sub-components in `React.memo`.

## 2025-05-20 - Unstable Callback Dependencies Invalidating Memoized Child Navigation
**Learning:** Passing unstable callback functions to memoized navigation components (`Sidebar` wrapped in `React.memo`) causes full component tree re-renders whenever state objects change. Additionally, triggering state updates (`setActiveSection`) that already run side-effects in `useEffect` creates duplicate API calls.
**Action:** Memoize API handlers with `useCallback` and keep section navigation callbacks clean with empty dependency arrays `[]` so memoized children skip re-renders.

## 2025-05-21 - N+1 Query Elimination in Storyboard DB Hierarchy
**Learning:** Building nested tree structures (e.g. Episode -> Scenes -> Panels) by issuing separate queries for child entities inside loops causes severe N+1 database connection churn and query multiplication. Batch-fetching child entities using `IN (SELECT ...)` within a single read connection reduces DB roundtrips from O(N) to 3 queries.
**Action:** Batch child queries using `SQL IN` subqueries within a single context manager session and group child records into a `defaultdict(list)` dictionary in memory before attaching to parent trees.

## 2026-09-26 - Rollup Manual Chunks & Image Lazy Loading
**Learning:** Monolithic Vite production bundles containing heavy UI chart libraries (Recharts) degrade initial script parse times and trigger build warnings (>500kB). Configuring Rollup `manualChunks` in `vite.config.ts` using module path checks (`id.includes('node_modules/recharts')`) splits dependencies into separate cacheable chunks, reducing the main application JS bundle size by >90% (615kB down to 58kB).
**Action:** Use functional `manualChunks` inspection in `vite.config.ts` for large third-party libraries (`recharts`, `react-dom`), and add `loading="lazy"` with explicit `width`/`height` dimensions to offscreen images.

## 2026-09-27 - Consolidated Simulation Timers & Ref Target Tracking in Interactive Canvas Components
**Learning:** Running multiple un-synchronized `setInterval` timers within interactive UI simulation components causes competing React state updates and 50% extra timer wakeups per second. Additionally, using object state as an interval dependency forces teardown/re-creation of the timer on every position move. Note that wrapping primitive scalar math (`Math.hypot`) in `useMemo` is a React anti-pattern that adds overhead compared to direct calculation.
**Action:** Unify simulation physics and jitter updates into a single 100ms interval timer with atomic state update callbacks, use `useRef` to track target position updates without restarting intervals, and calculate scalar distance metrics directly.
