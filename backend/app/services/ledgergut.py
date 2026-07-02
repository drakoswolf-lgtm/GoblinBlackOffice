"""
Ledgergut extraction service — receipt_reimbursement case type.

Given a file path to a receipt (PDF or image), Ledgergut:
  1. Attempts to read text from the file.
  2. Applies regex heuristics to locate vendor, date, and total.
  3. Returns an ExtractedData payload with a confidence score and any warnings.

For binary images (JPEG, PNG, etc.) where text extraction is not possible,
Ledgergut returns a low-confidence placeholder and flags the case for careful
human review.

DESIGN NOTE: This module is intentionally self-contained so that future
goblins can follow the same pattern:
  - create services/<goblin_name>.py
  - expose a single `extract(file_path) -> ExtractedData` coroutine
  - register the goblin in models/goblin.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Optional

from app.models.case import ExtractedData

# ---------------------------------------------------------------------------
# Regex patterns for receipt parsing
# ---------------------------------------------------------------------------

# Vendor: first non-blank line that looks like a business name
_VENDOR_RE = re.compile(
    r"^([A-Z][A-Za-z0-9\s&',.\-]{2,50})$", re.MULTILINE
)

# Date: common formats  MM/DD/YYYY  DD-MM-YYYY  Month DD, YYYY  YYYY-MM-DD
_DATE_RE = re.compile(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}"
    r"|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
    r"|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)

# Total: last dollar amount on the receipt (greedy — picks the highest line)
_TOTAL_RE = re.compile(
    r"(?:total|amount\s+due|grand\s+total|balance\s+due)[^\d$]*\$?\s*([\d,]+\.\d{2})",
    re.IGNORECASE,
)
# Fallback: any dollar amount
_AMOUNT_RE = re.compile(r"\$\s*([\d,]+\.\d{2})")


def _extract_from_text(text: str) -> ExtractedData:
    warnings: list[str] = []
    confidence_parts: list[float] = []

    # ── Vendor ──────────────────────────────────────────────────────────────
    vendor: Optional[str] = None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in lines[:8]:  # vendor usually near the top
        if _VENDOR_RE.match(line) and len(line) > 3:
            vendor = line
            break
    if vendor:
        confidence_parts.append(0.9)
    else:
        warnings.append("Could not identify vendor name.")
        confidence_parts.append(0.1)

    # ── Date ────────────────────────────────────────────────────────────────
    date: Optional[str] = None
    date_match = _DATE_RE.search(text)
    if date_match:
        date = date_match.group(1)
        confidence_parts.append(0.9)
    else:
        warnings.append("Could not identify transaction date.")
        confidence_parts.append(0.1)

    # ── Total ────────────────────────────────────────────────────────────────
    total: Optional[float] = None
    total_match = _TOTAL_RE.search(text)
    if total_match:
        try:
            total = float(total_match.group(1).replace(",", ""))
            confidence_parts.append(0.95)
        except ValueError:
            pass
    if total is None:
        # fallback: take the largest dollar amount found
        amounts = [
            float(m.group(1).replace(",", "")) for m in _AMOUNT_RE.finditer(text)
        ]
        if amounts:
            total = max(amounts)
            warnings.append("Total inferred from largest dollar amount on receipt.")
            confidence_parts.append(0.6)
        else:
            warnings.append("Could not identify a total amount.")
            confidence_parts.append(0.1)

    # ── Confidence ───────────────────────────────────────────────────────────
    confidence = round(sum(confidence_parts) / len(confidence_parts), 2) if confidence_parts else 0.0

    return ExtractedData(
        vendor=vendor,
        date=date,
        total=total,
        raw_text=text[:2000],  # store first 2 kB for debugging
        confidence=confidence,
        warnings=warnings,
    )


def _read_pdf_text(path: Path) -> Optional[str]:
    """Attempt to extract text from a PDF using pypdf."""
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception:
        return None


def extract(file_path: str) -> ExtractedData:
    """
    Main entry-point called by the cases router.

    Returns an ExtractedData instance regardless of file type.
    Adds warnings for low-confidence or unsupported formats.
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    # ── PDF ──────────────────────────────────────────────────────────────────
    if ext == ".pdf":
        text = _read_pdf_text(path)
        if text and text.strip():
            return _extract_from_text(text)
        return ExtractedData(
            confidence=0.15,
            warnings=[
                "PDF appears to be image-only (scanned). "
                "Text extraction not available — please fill in details manually."
            ],
        )

    # ── Plain text (testing / dev) ────────────────────────────────────────
    if ext in (".txt", ".csv"):
        text = path.read_text(errors="replace")
        return _extract_from_text(text)

    # ── Image formats ─────────────────────────────────────────────────────
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"):
        return ExtractedData(
            confidence=0.1,
            warnings=[
                f"Image file ({ext}) submitted. "
                "Optical character recognition is not yet available. "
                "Please fill in all fields manually."
            ],
        )

    # ── Unknown ───────────────────────────────────────────────────────────
    return ExtractedData(
        confidence=0.0,
        warnings=[
            f"Unsupported file type '{ext}'. "
            "Please upload a PDF, image (JPEG/PNG), or text file."
        ],
    )
