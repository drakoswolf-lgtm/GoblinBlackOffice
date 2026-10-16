# Receipt intake: holographic controls

The receipt entry choices now use one scoped projection treatment: dark glass,
cyan corner brackets, static scanlines, matching SVG line icons and left-aligned
bold italic labels. The cyan belongs to the projected interface above the
physical Office, consistent with the specialist channel treatment. All three
choices have equal heights and grow with enlarged text. They stack below 900px.

Upload is a native button with keyboard support and an accessible name and hint.
The review screen's image replacement action also uses a keyboard-accessible button.
It opens the existing native file chooser, stops an open camera and clears the
camera-only capture hint before selecting a gallery image. Manual entry moves
focus to Vendor. Existing scanning, multipart submission and human review remain
the workflow. No animation or speech was added.

Local verification on 2026-10-15:

- 204 Python tests passed.
- Chromium at 1440, 1024, 768, 390 and 320 CSS pixels: equal touch targets,
  readable content, no horizontal overflow, including 200% root text size.
- Keyboard order, visible focus, Enter/Space native file chooser and manual-entry focus passed.
- Camera permission denial, gallery capture-hint reset, actual multipart image
  upload and real Tesseract OCR review passed (test receipt total: CAD 26.88).
- Scoped axe WCAG A/AA checks reported no violations at all five widths.
- Forced colors and reduced transparency fallbacks passed; no page script errors.

Camera hardware capture and physical Android/iOS devices were not exercised.
The complete startup-film browser suite was not rerun locally for this scoped change.
Its existing upload smoke check now targets the native Upload Image button.

[Desktop preview](assets/receipt-controls-1440.jpg) ·
[Phone preview](assets/receipt-controls-390.jpg)
