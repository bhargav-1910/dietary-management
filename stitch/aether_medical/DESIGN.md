# Design System Document

## 1. Overview & Creative North Star: "The Clinical Sanctuary"

In the high-stakes environment of medical management, visual noise is the enemy of precision. This design system moves beyond the "utilitarian grid" to embrace **The Clinical Sanctuary**—a philosophy that treats software as a calming, high-end environment rather than a dense data table.

We reject the traditional "box-in-a-box" medical UI. Instead, we use **Intentional Asymmetry** and **Tonal Depth** to guide the eye. By utilizing a sophisticated scale of whites and soft blues, we create a sense of "Breathable Authority." The layout doesn't just display data; it curates it, using expansive white space and high-contrast editorial typography to elevate critical patient information from "rows of text" to "points of focus."

---

## 2. Colors & Surface Philosophy

The palette is rooted in medical trust but executed with the sophistication of a premium lifestyle brand.

### The "No-Line" Rule
Standard 1px borders are strictly prohibited for defining sections. They create visual "cages" that fatigue the eye. Instead, boundaries are defined by **Background Color Shifts**. A patient's chart (Surface Container Lowest) should sit on a clinic dashboard (Surface) purely through the contrast of their hex values.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers of fine paper or frosted glass.
- **Surface (#f8f9fa):** The base canvas.
- **Surface-Container-Low (#f3f4f5):** Used for secondary layout areas like the sidebar background.
- **Surface-Container-Lowest (#ffffff):** Reserved for primary interactive cards to create a "natural lift."
- **Surface-Container-Highest (#e1e3e4):** Used for inactive states or subtle "sunken" areas like search bars.

### The "Glass & Gradient" Rule
To avoid a "flat" corporate feel, use **Glassmorphism** for floating elements (modals, popovers). Use `surface_container_lowest` at 80% opacity with a `12px` backdrop blur. For primary CTAs, apply a subtle linear gradient from `primary` (#005da7) to `primary_container` (#2976c7) at a 135-degree angle to provide a "jewel" polish.

---

## 3. Typography: Editorial Authority

We use a dual-font strategy to balance human warmth with clinical precision.

*   **Display & Headlines (Manrope):** A geometric sans-serif that feels modern and authoritative. Use `display-md` for patient names or high-level clinic metrics to create an "editorial" feel.
*   **Body & Labels (Inter):** The workhorse. Inter’s tall x-height ensures readability of complex medical terms even at `body-sm` (0.75rem).

**The Scale Principle:** Use extreme contrast. A `headline-lg` title should be immediately followed by `body-md` metadata. This "Big-Small" pairing removes the need for bold lines and helps the clinician scan pages 40% faster.

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering** rather than structural lines. Place a `surface_container_lowest` card on a `surface_container_low` background. The shift from `#ffffff` to `#f3f4f5` creates a crisp, sophisticated edge without a single pixel of "ink."

### Ambient Shadows
Shadows must be invisible until noticed.
- **Elevation 1 (Cards):** `0 4px 20px -2px rgba(25, 28, 29, 0.04)`.
- **Elevation 2 (Modals):** `0 12px 40px -4px rgba(25, 28, 29, 0.08)`.
- *Shadow Color Tip:* Use a tint of `on_surface` (#191c1d) rather than pure black to keep the UI feeling "airy."

### The "Ghost Border" Fallback
If a container requires a boundary (e.g., a text input), use a **Ghost Border**: `outline_variant` (#c1c7d3) at 20% opacity. 100% opaque borders are forbidden.

---

## 5. Signature Components

### Cards & Data Clusters
*   **Design Rule:** Forbid divider lines. Use `spacing-6` (1.5rem) of vertical white space to separate content groups.
*   **Style:** `roundness-lg` (1rem), `surface_container_lowest` background, and Elevation 1 ambient shadow.

### Buttons (The "Soft Command")
*   **Primary:** Gradient of `primary` to `primary_container`. `roundness-full` (pill shape).
*   **Secondary:** `surface_container_high` background with `on_primary_fixed_variant` text. No border.
*   **States:** On hover, increase the gradient intensity; on press, scale the button down to 0.98 for tactile feedback.

### Input Fields
*   **Design:** `surface_container_low` background with a `roundness-md` (0.75rem).
*   **Interaction:** On focus, the background transitions to `surface_container_lowest` and a 2px "Ghost Border" of `primary` appears.

### The Sanctuary Sidebar (Navigation)
*   **Design:** Fixed vertical sidebar using `surface_container_low`. 
*   **Icons:** Use "Thin" weight icons (2px stroke) in `on_surface_variant`. 
*   **Active State:** The active item should not have a box; it should have a `primary` colored vertical "indicator pill" (4px width) on the far left and the text should shift to `primary` color.

### Contextual "Pulse" Chips
*   **Usage:** For patient status (e.g., "In Progress").
*   **Style:** Use `secondary_container` background with `on_secondary_container` text. Apply a `roundness-full` and include a small 6px solid dot (the "pulse") of the `secondary` color.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use `spacing-10` and `spacing-12` for section margins. Medical data needs "room to breathe" to prevent diagnostic errors.
*   **Do** use `tertiary` (#7f5300) for "Attention Required" states rather than immediate `error` red, to keep the clinic atmosphere calm.
*   **Do** overlap elements. Let a patient's profile photo slightly "break" the top edge of a card to create a high-end, custom-built feel.

### Don't
*   **Don't** use 100% black text. Always use `on_surface` (#191c1d) to reduce eye strain during long shifts.
*   **Don't** use standard tables with grid lines. Use "Floating Lists" where each row is a subtle `surface_container_low` shape with `roundness-sm`.
*   **Don't** use sharp corners. Use `roundness-DEFAULT` (0.5rem) as the absolute minimum to maintain the "Sanctuary" softness.