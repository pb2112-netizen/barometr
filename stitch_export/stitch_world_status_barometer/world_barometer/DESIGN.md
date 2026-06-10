---
name: World Barometer
colors:
  surface: '#fcf8fa'
  surface-dim: '#dcd9db'
  surface-bright: '#fcf8fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f5'
  surface-container: '#f0edef'
  surface-container-high: '#eae7e9'
  surface-container-highest: '#e4e2e4'
  on-surface: '#1b1b1d'
  on-surface-variant: '#45464d'
  inverse-surface: '#303032'
  inverse-on-surface: '#f3f0f2'
  outline: '#76777d'
  outline-variant: '#c6c6cd'
  surface-tint: '#565e74'
  primary: '#000000'
  on-primary: '#ffffff'
  primary-container: '#131b2e'
  on-primary-container: '#7c839b'
  inverse-primary: '#bec6e0'
  secondary: '#505f76'
  on-secondary: '#ffffff'
  secondary-container: '#d0e1fb'
  on-secondary-container: '#54647a'
  tertiary: '#000000'
  on-tertiary: '#ffffff'
  tertiary-container: '#271901'
  on-tertiary-container: '#98805d'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae2fd'
  primary-fixed-dim: '#bec6e0'
  on-primary-fixed: '#131b2e'
  on-primary-fixed-variant: '#3f465c'
  secondary-fixed: '#d3e4fe'
  secondary-fixed-dim: '#b7c8e1'
  on-secondary-fixed: '#0b1c30'
  on-secondary-fixed-variant: '#38485d'
  tertiary-fixed: '#fcdeb5'
  tertiary-fixed-dim: '#dec29a'
  on-tertiary-fixed: '#271901'
  on-tertiary-fixed-variant: '#574425'
  background: '#fcf8fa'
  on-background: '#1b1b1d'
  surface-variant: '#e4e2e4'
typography:
  score-display:
    fontFamily: Hanken Grotesk
    fontSize: 120px
    fontWeight: '700'
    lineHeight: 110px
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 8px
  container-padding: 24px
  stack-gap-sm: 12px
  stack-gap-md: 24px
  stack-gap-lg: 48px
  max-width: 600px
---

## Brand & Style
The design system is rooted in **Minimalism** with a **Corporate/Modern** backbone. It prioritizes data integrity and rapid comprehension over decorative flair. The aesthetic is inspired by high-end weather applications and institutional financial terminals—stripping away visual noise to focus on the "Risk Score."

The emotional response should be one of objective clarity. It avoids alarmism, even when displaying high-risk data, by using a structured, airy layout and precise typography. The interface feels like a precision instrument: reliable, quiet, and authoritative.

**Key Principles:**
- **Data-First:** The score is the hero; all other elements are secondary.
- **Breathable:** High use of whitespace to reduce cognitive load during complex geopolitical analysis.
- **Dynamic Status:** The interface adapts its semantic accent to the severity of the data, providing an immediate pre-attentive signal of the situation.

## Colors
The palette is dominated by a neutral "Slate" scale to maintain a professional, utility-centric atmosphere. The primary color is a deep, authoritative ink used for text and primary branding. 

**Dynamic Accents:**
The "Accent" color is functional rather than aesthetic. It must shift globally based on the active risk level:
- **Low (1-3):** Emerald Green. Signals stability and calm.
- **Elevated (4-6):** Amber. Signals caution and surveillance.
- **High (7-10):** Crimson. Signals crisis or active conflict.

**Dark Mode:**
In dark mode, the background shifts to a deep charcoal (`#020617`), and surface containers use a slightly lighter slate (`#1E293B`). Contrast ratios for semantic colors must be adjusted to ensure legibility against dark surfaces while maintaining their "warning" intent.

## Typography
The typographic system uses **Hanken Grotesk** for headlines and data displays to provide a sharp, contemporary look that feels like a modern newsroom. **Inter** is used for body text and UI labels due to its exceptional legibility and systematic, utilitarian feel.

**The Score Display:**
The primary risk score uses a massive, bold weight with tight letter-spacing to command immediate attention. This is the "hero" of the layout and should be centered or prominently placed at the top of the view.

**Labels:**
Metadata (e.g., "Last Updated," "Region," "Trend") should use the `label-caps` style to differentiate secondary information from the primary narrative text.

## Layout & Spacing
The layout follows a **fluid grid** logic optimized for mobile-first consumption. Since the content is utility-driven, it uses a single-column vertical stack with generous top-and-bottom margins to keep the focus central.

- **Margins:** A standard 24px horizontal margin ensures content doesn't feel cramped on small screens.
- **Rhythm:** An 8px base unit governs all spacing. Use 48px (6 units) between major sections (Score vs. Map vs. Analysis) and 12px or 24px for internal element grouping.
- **Safe Areas:** Ensure the score is positioned safely below the status bar to allow the "color flood" (the semantic background tint) to feel immersive.

## Elevation & Depth
This design system avoids heavy shadows and skeuomorphism. Depth is achieved through **Tonal Layers** and **Low-contrast Outlines**.

- **Surfaces:** Use subtle background shifts (e.g., a white card on a light grey background) to define containers.
- **Outlines:** Elements like input fields or secondary cards use 1px borders in a soft neutral (`#E2E8F0` in light mode).
- **Active State:** Only the most critical interaction points (like an "Alert" toggle) may use a soft, diffused shadow to indicate prominence. Otherwise, keep the UI flat to maintain the "Barometer" feel.

## Shapes
The shape language is **Soft** (0.25rem - 0.75rem). This introduces enough friendliness to prevent the app from feeling "hostile" or "militaristic," while remaining professional and structured.

- **Small Components:** Checkboxes and small buttons use the 0.25rem (4px) radius.
- **Large Components:** Data cards and bottom sheets use the 0.75rem (12px) radius.
- **Score Indicators:** Trend arrows and badges use the standard 4px radius to maintain a cohesive technical look.

## Components
**Buttons:**
Primary buttons are solid blocks of the current semantic accent color (Green/Amber/Red) with white text. Secondary buttons are outlined in Slate-300 with Slate-900 text.

**The Barometer Gauge:**
A custom component. A horizontal thin line with a sliding "needle" or a segmented 1-10 bar. The active segment should glow slightly with the semantic color, while inactive segments remain a muted grey.

**Risk Cards:**
Used for regional breakdowns. They should be clean, with the region name on the left and a small, bold score badge on the right. The badge background color must match the semantic risk level.

**Inputs:**
Text inputs are minimal—just a bottom border or a very light 4px rounded box. Focus states are indicated by a 2px stroke of the current semantic accent color.

**Trend Indicators:**
Small arrows (up/down/stable) next to the score. Use the semantic color for the arrow itself to indicate whether risk is increasing (Red) or decreasing (Green), independent of the current absolute score.