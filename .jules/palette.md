## 2024-08-28 - Chat Form Accessibility & Input Validation Feedback
**Learning:** Embedded chat widgets require explicit `aria-label` attributes on inputs/buttons, visible focus states (`focus-visible:ring-2`), and validation checks (`input.trim()`) on both click and `Enter` keydown events to prevent empty message submission and preserve keyboard navigation accessibility.
**Action:** When enhancing form controls in chat widgets, pair `aria-label` and `focus-visible` ring styles with disabled button states and visual loading spinners for async message delivery.

## 2026-09-03 - Dynamic Stencil Canvas & AR Overlay Live Feedback
**Learning:** Interactive stencil generators and dynamic overlay tools benefit from an `aria-live="polite"` feedback container that dynamically announces seed variations, AR mode toggles, and file downloads for screen reader users while providing instant feedback.
**Action:** When adding or updating custom canvas or SVG generation tools, include an `aria-live="polite"` status region with explicit state announcements alongside `aria-label` attributes on range inputs and toggle buttons.

## 2026-09-09 - Collapsible Floating AI Chat Widget & Flex Container Constraints
**Learning:** Floating overlay widgets (like AI chat windows) require collapse/expand controls with explicit `aria-expanded` and `aria-label` states to allow users to unblock background telemetry charts. When styling flex containers within fixed-width cards (`w-80`), `<input>` controls require `min-w-0` to prevent flex items from expanding past container bounds and truncating submit buttons.
**Action:** Always add `aria-expanded` toggle controls to fixed floating overlays and apply `min-w-0` to flex input elements inside fixed-width containers.
