## 2025-05-18 - Scroll Handler Layout Thrashing & Unmemoized Chart Components
**Learning:** High-frequency scroll event listeners reading DOM element geometry (`offsetTop`, `offsetHeight`) cause layout thrashing and high main-thread CPU usage on every scroll pixel. Unmemoized Recharts components re-render heavy SVG trees whenever active section state updates.
**Action:** Throttle scroll listeners with `requestAnimationFrame` and `{ passive: true }`, and wrap SVG chart components in `React.memo` to skip redundant re-renders.
