## 2024-08-28 - Chat Form Accessibility & Input Validation Feedback
**Learning:** Embedded chat widgets require explicit `aria-label` attributes on inputs/buttons, visible focus states (`focus-visible:ring-2`), and validation checks (`input.trim()`) on both click and `Enter` keydown events to prevent empty message submission and preserve keyboard navigation accessibility.
**Action:** When enhancing form controls in chat widgets, pair `aria-label` and `focus-visible` ring styles with disabled button states and visual loading spinners for async message delivery.

## 2026-09-03 - Dynamic Stencil Canvas & AR Overlay Live Feedback
**Learning:** Interactive stencil generators and dynamic overlay tools benefit from an `aria-live="polite"` feedback container that dynamically announces seed variations, AR mode toggles, and file downloads for screen reader users while providing instant feedback.
**Action:** When adding or updating custom canvas or SVG generation tools, include an `aria-live="polite"` status region with explicit state announcements alongside `aria-label` attributes on range inputs and toggle buttons.

## 2026-09-05 - Floating Chat Widget Collapsibility & Expandability
**Learning:** Floating overlay components (like AI chat assistants) can obscure data charts and interactive canvas areas on smaller viewports. Providing an explicit minimize/expand toggle button with `aria-expanded` and `aria-label` attributes ensures screen reader accessibility while allowing users to reclaim screen real estate without losing active conversation state.
**Action:** When creating or updating floating overlay UI elements, include a toggle button with `aria-expanded` and `focus-visible:ring-2` focus styling to support viewport customization and keyboard accessibility.

## 2026-09-08 - Interactive Canvas Trajectory Alignment & Live Accessibility Feedback
**Learning:** Real-time canvas simulations benefit from instantaneous visual accuracy metrics paired with explicit ARIA `role="region"` and `role="img"` attributes with dynamically computed `aria-label` values, providing clear feedback for all users during interactive simulations.
**Action:** When building interactive canvas or trajectory tracking tools, include a live accuracy badge with color-coded feedback states and explicit ARIA descriptors.
