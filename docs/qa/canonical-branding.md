# Canonical logo rollout

The approved `resources/canon/brand/canon-app-badge.webp` is the single source for
the application identity. Its geometry, orientation and material treatment are
unchanged. The ImageGen placement preview is illustrative; production uses the
original badge bytes, not a generated replacement.

The shared `gbo/brand.html` macro replaces GBO, LG, SQ and SN letter tiles on
registration, sign-in, new-job, document settings and specialist workspaces.
It also unifies existing Command Desk, Æterna, records and project header logos,
and adds an Office identity to workflow guides. The existing onboarding and
environment badges remain in place. First-entry films are unchanged.

All full HTML screens include shared browser-icon and touch-icon metadata.
PNG and ICO derivatives are deterministic resizes of the approved badge.
Shared templates are explicitly namespaced and available to all four mounted
Flask applications without replacing their own template loaders. Static and
canonical image URLs are root-relative so specialist routes resolve them correctly.

Header images retain square dimensions and contain-fit rendering. Their text
wordmarks provide accessible link names; decorative badge images have empty alt
text. Explicit image dimensions reserve space before decoding. Brand links have
visible keyboard focus, wrap at narrow widths and support forced colors.

Business-owned logos in invoice/agreement PDFs and document settings retain their
existing behavior; the app badge is not substituted for a customer's identity.

Local verification on 2026-10-15:

- 204 Python tests passed after wiring the shared loaders and templates.
- Chromium: 13 public/workspace routes at 1440, 768, 390 and 320 CSS pixels,
  checking successful responses, logo decoding, intact square proportions,
  root-relative assets, wordmark bounds and keyboard focus.
- Registration at 200% root text size passed at each width.
- Scoped axe WCAG A/AA checks on registration and receipt header links found no violations.
- Real temporary account: first-entry metadata and onboarding badge passed.
- A real temporary client/project workbench rendered the shared logo successfully.
- Every favicon/touch-icon endpoint returned its image format; forced colors and
  page script error checks passed.

These are local Chromium checks. Live deployment, physical mobile devices and
operating-system icon installation have not been verified.

[Registration on phone](assets/brand-registration-390.jpg) ·
[Receipts on phone](assets/brand-receipts-390.jpg)
