---
name: Clinical Monochrome
colors:
  surface: '#f9f9f9'
  surface-dim: '#dadada'
  surface-bright: '#f9f9f9'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f4f3f3'
  surface-container: '#eeeeee'
  surface-container-high: '#e8e8e8'
  surface-container-highest: '#e2e2e2'
  on-surface: '#1a1c1c'
  on-surface-variant: '#444748'
  inverse-surface: '#2f3131'
  inverse-on-surface: '#f1f1f1'
  outline: '#747878'
  outline-variant: '#c4c7c7'
  surface-tint: '#5f5e5e'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#1c1b1b'
  on-primary-container: '#858383'
  inverse-primary: '#c9c6c5'
  secondary: '#5e5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e1dfdf'
  on-secondary-container: '#626262'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#1d1b1a'
  on-tertiary-container: '#868381'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e5e2e1'
  primary-fixed-dim: '#c9c6c5'
  on-primary-fixed: '#1c1b1b'
  on-primary-fixed-variant: '#474646'
  secondary-fixed: '#e4e2e2'
  secondary-fixed-dim: '#c7c6c6'
  on-secondary-fixed: '#1b1c1c'
  on-secondary-fixed-variant: '#464747'
  tertiary-fixed: '#e6e1df'
  tertiary-fixed-dim: '#cac6c3'
  on-tertiary-fixed: '#1d1b1a'
  on-tertiary-fixed-variant: '#484645'
  background: '#f9f9f9'
  on-background: '#1a1c1c'
  surface-variant: '#e2e2e2'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.04em
  caption:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  data-metric:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 52px
    letterSpacing: -0.03em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-mobile: 1rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
  space-2xl: 4rem
---

## Brand & Style

This design system delivers clinical precision, objective clarity, and unwavering calm for an educational medical screening environment. Grounded in functional minimalism and editorial medical publishing, the aesthetic removes all extraneous ornamentation, glowing effects, and chromatic distractions.

The emotional tone is authoritative, diagnostic, and serene. It eliminates medical anxiety caused by alarming alert tones (such as aggressive ambers or reds) by translating diagnostic risk entirely into structured monochromatic contrast, line weights, iconography, and explicit typographic labeling. The interface prioritizes scannability, legibility, and high-trust delivery of sensitive health calculations.

## Colors

The palette operates under a strict achromatic constraint. No hues, saturations, or color tints are permitted under any condition.

- **Primary Canvas (`#FFFFFF`):** Base canvas for maximum text-to-background contrast ratio (exceeding 18:1).
- **Secondary Canvas (`#F5F5F5`):** Subtle off-white for section segregation, data tables, well-containers, and non-interactive backgrounds.
- **Primary Text & Solids (`#0A0A0A`):** Deep black utilized for headlines, primary buttons, dominant data points, active toggles, and high-risk classifications.
- **Secondary / Supporting (`#6B6B6B`):** Balanced mid-gray for labels, descriptive metadata, input placeholders, and inactive states. Maintains a minimum 4.5:1 WCAG AA contrast ratio against white.
- **Structural Outlines & Rules (`#E5E5E5`):** Light gray assigned strictly to 1px hair lines, card wrappers, divider rules, and unfocused form fields.

### Risk Stratification Tokens (Achromatic Patterning)
Risk level indicators rely entirely on visual density, geometry, and labeling rather than color:
- **Low Risk:** Single 1px solid `#E5E5E5` border with an inverted white pill badge containing `#0A0A0A` text and an open circle icon (`○`).
- **Moderate Risk:** 1.5px dashed `#6B6B6B` border, `#F5F5F5` background, with a half-filled dot icon (`◐`).
- **Elevated / High Risk:** Solid 2px `#0A0A0A` outer border, solid `#0A0A0A` badge with `#FFFFFF` text, and a solid filled disc icon (`●`).

## Typography

Typographic scale and hierarchy are executed exclusively through weight distribution, tabular figures, and calibrated optical spacing using Inter.

All statistical outputs, lab values, and clinical scores must use OpenType tabular figure features (`tnum`) to maintain structural vertical alignment across comparisons. Headings emphasize deliberate, surgical authority through tight letter tracking, while long-form advisory copy retains relaxed line spacing to enhance cognitive ease during stressful diagnostic reading.

## Layout & Spacing

The layout philosophy follows a disciplined 12-column responsive fluid grid anchored by strict vertical rhythm. Screening wizards and risk assessment modules are centered within an 8-column reading well (maximum 768px width) to minimize horizontal eye travel and reduce intake fatigue.

- **Desktop (1024px+):** 12 columns, 1.5rem (`24px`) gutters, minimum 2rem outer margins. Dashboard and comparative metrics leverage a split 6/6 or 4/8 asymmetric structural layout.
- **Tablet (768px - 1023px):** 8 columns, 1rem (`16px`) gutters, 1.5rem margins.
- **Mobile (< 768px):** 4 columns, 1rem gutters, 1rem outer margins. Multi-step forms reflow to a 100% full-width single-column flow with pinned sticky bottom actions.

## Elevation & Depth

Visual hierarchy does not use blur-heavy drop shadows or tonal elevation planes. The system is structurally flat, relying on crisp 1px borders and razor-thin ambient occlusion.

- **Level 0 (Flat Canvas):** Surfaces sit directly on `#FFFFFF` or `#F5F5F5` with no shadow. Structural division is handled exclusively by a 1px border of `#E5E5E5`.
- **Level 1 (Cards, Selectors, Panels):** 1px solid border (`#E5E5E5`) supplemented by an ultra-subtle, clean gray shadow: `0 1px 3px rgba(10, 10, 10, 0.04), 0 1px 2px rgba(10, 10, 10, 0.02)`.
- **Level 2 (Active Modals, Floating Metric Drawers):** 1px solid border (`#0A0A0A`) complemented by a targeted soft shadow: `0 4px 12px rgba(10, 10, 10, 0.06), 0 1px 3px rgba(10, 10, 10, 0.04)`.
- **Level 3 (Diagnostic Focus / Overlays):** Modal backdrops use `#0A0A0A` at 40% solid opacity with no backdrop-filter blur, enforcing a crisp, photographic vignette.

## Shapes

The interface embraces a restrained "Soft" corner geometry (`0.25rem` / `4px`). This slight softening removes the raw severity of 0px brutalism while avoiding the playful, consumerist casualness of larger radii or pill shapes.

Interactive controls, cards, input text boxes, and table containers share a 4px corner radius. Badges and structural indicator chips default to 2px or 4px radii. Circular elements are restricted strictly to radio buttons, status glyphs, and numerical step trackers.

## Components

### Buttons
- **Primary:** Background `#0A0A0A`, text `#FFFFFF`, 4px radius, no border. Hover shifts background to `#262626`. Focus state exhibits an outer 2px offset ring in `#0A0A0A`.
- **Secondary:** Background `#FFFFFF`, 1px solid `#0A0A0A`, text `#0A0A0A`. Hover state shifts background to `#F5F5F5`.
- **Tertiary / Ghost:** Background transparent, text `#6B6B6B`, underlined on hover with text transitioning to `#0A0A0A`.

### Input Fields & Selects
- 1px solid `#E5E5E5` border on `#FFFFFF` base, 4px radius. 
- Placeholder text in `#6B6B6B`.
- Focused state replaces border with a precise 1.5px solid `#0A0A0A` without colorful glow rings.
- Inline validation errors are rendered with a 1.5px `#0A0A0A` underline and an explicit icon-prefixed warning label in `#0A0A0A` bold typography.

### Checkboxes & Radio Buttons
- **Checkbox:** Square box with 2px radius, 1.5px border `#0A0A0A`. Checked state fills `#0A0A0A` with a crisp `#FFFFFF` checkmark.
- **Radio Button:** 16px circular boundary, 1.5px `#0A0A0A` ring. Active selection renders an inner solid concentric circle of 8px `#0A0A0A`.

### Cards & Result Wells
- Standard cards feature a `#FFFFFF` fill with a continuous 1px `#E5E5E5` hairline border and Level 1 elevation.
- Data highlight wells (e.g., patient calculation summary) use `#F5F5F5` background with an inset 1px `#E5E5E5` border and no drop shadow.

### Chips & Risk Badges
- **Informational Chips:** 4px radius, `#F5F5F5` background, `#0A0A0A` text, 1px `#E5E5E5` border.
- **Stratification Result Badges:**
  - *Normal:* `#FFFFFF` fill, 1px solid `#6B6B6B` border, text `#0A0A0A`.
  - *Borderline:* 1.5px dashed border `#0A0A0A`, text `#0A0A0A`, `#FFFFFF` fill.
  - *High Concern:* Solid `#0A0A0A` fill, text `#FFFFFF`, bold tracking.

### Assessment Sliders & Question Steppers
- Horizontal range tracks use a 2px solid `#E5E5E5` line with `#0A0A0A` progress fill.
- Sliders use a solid `#0A0A0A` disc thumb with an outer 2px `#FFFFFF` halo.
- Question pagination displays step indicators as sequential monochrome segments: active step is solid `#0A0A0A`, completed is `#6B6B6B`, upcoming is `#E5E5E5`.