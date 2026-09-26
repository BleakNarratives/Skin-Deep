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

## 2026-09-17 - SVG Data Chart Accessibility & Dynamic AI Live Regions
**Learning:** Complex SVG data charts (such as Recharts line graphs) are read as unlabelled graphics by screen readers unless wrapped in a container with `role="img"` and a descriptive `aria-label`. Similarly, asynchronous AI section insights require an `aria-live="polite"` region with `aria-atomic="true"` to announce content updates when switching sections without disrupting the screen reader cursor.
**Action:** Wrap chart containers with `role="img"` and descriptive `aria-label` strings, and enclose asynchronous AI status containers in `aria-live="polite"` containers with `aria-hidden="true"` on decorative loading spinners.

## 2026-09-22 - Interactive Simulation Canvas & Relative Target Positioning
**Learning:** 2D simulation canvas surfaces require `role="region"`, `tabIndex={0}`, and clear `aria-label` descriptors explaining interaction semantics. Overlay text must use `pointer-events-none` so mouse clicks are registered on the surface container, and explicit reset controls with `focus-visible:ring-2` styling ensure full keyboard accessibility and easy state reset.
**Action:** When making canvas/simulation areas interactive, apply `role="region"`, `aria-label`, `pointer-events-none` on overlay elements, and pair with an accessible Reset button.
