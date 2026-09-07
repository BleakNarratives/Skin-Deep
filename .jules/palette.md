## 2024-08-28 - Chat Form Accessibility & Input Validation Feedback
**Learning:** Embedded chat widgets require explicit `aria-label` attributes on inputs/buttons, visible focus states (`focus-visible:ring-2`), and validation checks (`input.trim()`) on both click and `Enter` keydown events to prevent empty message submission and preserve keyboard navigation accessibility.
**Action:** When enhancing form controls in chat widgets, pair `aria-label` and `focus-visible` ring styles with disabled button states and visual loading spinners for async message delivery.

## 2026-09-03 - Dynamic Stencil Canvas & AR Overlay Live Feedback
**Learning:** Interactive stencil generators and dynamic overlay tools benefit from an `aria-live="polite"` feedback container that dynamically announces seed variations, AR mode toggles, and file downloads for screen reader users while providing instant feedback.
**Action:** When adding or updating custom canvas or SVG generation tools, include an `aria-live="polite"` status region with explicit state announcements alongside `aria-label` attributes on range inputs and toggle buttons.

## 2026-09-15 - Floating Collapsible Chat Widgets & Screen Reader Live Regions
**Learning:** Fixed overlay widgets (like floating AI chat interfaces) permanently obscure viewport content unless paired with a collapsible state (`isMinimized`), explicit `aria-expanded` and `aria-label` toggle attributes, focus-visible rings (`focus-visible:ring-2`), and `role="log"` with `aria-live="polite"` on message logs to ensure both visual clarity and screen reader awareness.
**Action:** Always provide minimize/expand capability for fixed bottom-corner UI components with accessible toggle controls and live region message containers.
