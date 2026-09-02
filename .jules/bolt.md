## 2025-05-18 - Scroll Handler Layout Thrashing & Unmemoized Chart Components
**Learning:** High-frequency scroll event listeners reading DOM element geometry (`offsetTop`, `offsetHeight`) cause layout thrashing and high main-thread CPU usage on every scroll pixel. Unmemoized Recharts components re-render heavy SVG trees whenever active section state updates.
**Action:** Throttle scroll listeners with `requestAnimationFrame` and `{ passive: true }`, and wrap SVG chart components in `React.memo` to skip redundant re-renders.

## 2025-05-19 - Unmemoized PRNG Path Generation in Interactive SVG Components
**Learning:** In interactive SVG stencil tools, slider inputs (like scale and opacity controls) trigger continuous re-renders. If geometric path algorithms using PRNG loops and trigonometric math (`Math.sin`, `Math.cos`) are not wrapped in `useMemo`, every drag tick recalculates complex path strings, causing frame drops during UI interactions.
**Action:** Wrap procedural path generation functions in `useMemo` dependent only on design seed/style parameters, and wrap interactive SVG sub-components in `React.memo`.
