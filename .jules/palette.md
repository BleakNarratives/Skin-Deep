## 2024-08-28 - Chat Form Accessibility & Input Validation Feedback
**Learning:** Embedded chat widgets require explicit `aria-label` attributes on inputs/buttons, visible focus states (`focus-visible:ring-2`), and validation checks (`input.trim()`) on both click and `Enter` keydown events to prevent empty message submission and preserve keyboard navigation accessibility.
**Action:** When enhancing form controls in chat widgets, pair `aria-label` and `focus-visible` ring styles with disabled button states and visual loading spinners for async message delivery.

## 2026-09-03 - Dynamic Stencil Canvas & AR Overlay Live Feedback
**Learning:** Interactive stencil generators and dynamic overlay tools benefit from an `aria-live="polite"` feedback container that dynamically announces seed variations, AR mode toggles, and file downloads for screen reader users while providing instant feedback.
**Action:** When adding or updating custom canvas or SVG generation tools, include an `aria-live="polite"` status region with explicit state announcements alongside `aria-label` attributes on range inputs and toggle buttons.

## 2026-09-05 - Floating Chat Widget Collapsibility & Expandability
**Learning:** Floating overlay components (like AI chat assistants) can obscure data charts and interactive canvas areas on smaller viewports. Providing an explicit minimize/expand toggle button with `aria-expanded` and `aria-label` attributes ensures screen reader accessibility while allowing users to reclaim screen real estate without losing active conversation state.
**Action:** When creating or updating floating overlay UI elements, include a toggle button with `aria-expanded` and `focus-visible:ring-2` focus styling to support viewport customization and keyboard accessibility.

## 2026-09-16 - Range Input ARIA Value Attributes
**Learning:** Interpolating variable numeric values directly inside `aria-label` on range inputs can cause screen readers to announce the full label name repeatedly as slider values change. Keeping `aria-label` static and using explicit `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and descriptive `aria-valuetext` provides precise value announcements for assistive technologies.
**Action:** On range inputs, pair static `aria-label` descriptors with `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and human-friendly `aria-valuetext` strings.

## 2026-09-18 - Mobile Drawer Navigation Accessibility & State Sync
**Learning:** When sidebars or navigation drawers are hidden on small screens (`lg:block`), adding a header toggle button with `aria-expanded`, `aria-controls="main-sidebar"`, and explicit `aria-label` ensures mobile users and screen readers can easily reveal navigation links. Auto-closing the drawer upon selecting a section prevents obscuring main view content.
**Action:** For responsive navigation drawers, connect the toggle button's `aria-controls` to the `<nav id="...">` element, manage `aria-expanded` state, and auto-close the drawer on item selection.
