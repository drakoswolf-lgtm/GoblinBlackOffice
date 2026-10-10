# Goblin Black Office Canon Image Library

These assets are approved visual canon. Product UI, animation work, onboarding, and future generative references should use this library rather than earlier exploratory renders.

## Startup / access sequence

- `startup/canon-startup-charge.webp` — approved G4 startup/loading charge keyframe.
- `startup/canon-access-door-closed.webp` — approved graphite access-door reveal.
- `startup/canon-access-door-opening.webp` — approved opening-door keyframe. The insignia is ONE continuous mark bisected by the vertical door plane; it must never be duplicated onto both door leaves.

The earlier doubled-logo opening render is intentionally excluded from canon.

## Cmdr. Æterna Skyeward

- `characters/canon-aeterna-command.webp` — approved command-environment character keyframe.
- `characters/canon-aeterna-headshot.webp` — approved straight-on persistent advice-box portrait.

Æterna remains collarless, wears the metallic HUD diadem, and uses cobalt/electric-blue command lighting rather than goblin green.

## Brand

- `brand/canon-app-badge.webp` — approved application badge treatment using the current angular right-facing bird insignia.

## Asset policy

These WebP files are repository-optimized canonical copies of the approved source renders. They are intended for UI reference, implementation, and responsive app use. Do not replace them with exploratory Artlist generations or superseded logo/bomb/Æterna concepts.

When a canon image is replaced by explicit approval, update this index in the same commit and preserve superseded work outside the canon paths.


## Approved static Black Office backgrounds

The command desk uses two **pixel-identical, lossless WebP encodings** of the approved artwork. These are physical-environment plates, not UI mockups. The interface panels and Æterna sit in front of them.

- `environments/canon-black-office-desktop.webp` — 1586 × 992 landscape, SHA-256 `2995be146bc0b8aaa6b973c04b5c7c31cdd2cbd6c6df1677953f854485f66aa1`.
- `environments/canon-black-office-mobile.webp` — 941 × 1672 portrait, SHA-256 `81c5dee12db7a09366dd661dfce573dc3873f9ed6a3f7e8364359becf41a645b`.

Render with CSS `background-size: cover` inside the fixed Office environment layer. Select the portrait plate at widths up to 700px. Do not crop or synthesize new artwork into these assets. The older `canon-black-office-command.svg` remains a fallback only. No additional animations are part of this change.
