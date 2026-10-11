"""Local, confidence-gated OCR for photographed Ledgergut receipts.

Receipts need contrast recovery and sensible page segmentation. Transcription is
never proof of purchase or an authorization to save: the user reviews fields.
"""

from __future__ import annotations

from io import BytesIO

class OcrError(Exception):
    """Raised when local OCR cannot produce a minimally useful transcription."""


def _quality(text: str) -> int:
    """Favor recognized receipt structure, not sheer quantity of OCR gibberish."""
    from app.ledgergut.receipt_parser import parse_receipt_text
    parsed = parse_receipt_text(text)
    score = 0
    if parsed.total_amount is not None:
        score += 7
    if parsed.subtotal is not None:
        score += 3
    if parsed.tax_amount is not None:
        score += 2
    if parsed.receipt_date is not None:
        score += 3
    if parsed.vendor_name is not None:
        score += 2
    if parsed.receipt_number is not None:
        score += 1
    return score


def extract_text_from_image(image_bytes: bytes) -> str:
    """Recover readable text from common thermal receipts and phone photographs.

    Tesseract's page segmentation 6 handles block-like receipts; mode 11 handles
    uneven smartphone shots. Try quarter-turns only if the upright result fails.
    Reject output that has no receipt structure rather than autofilling nonsense.
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise OcrError(
            "Local OCR is unavailable because the OCR dependencies are not installed."
        ) from exc

    try:
        with Image.open(BytesIO(image_bytes)) as source:
            source = ImageOps.exif_transpose(source)
            if source.width * source.height > 40_000_000:
                raise OcrError("That photo is too large to scan. Try a smaller image.")
            source = source.convert("RGB")
            source.thumbnail((3500, 3500), Image.Resampling.LANCZOS)
            grayscale = ImageOps.autocontrast(ImageOps.grayscale(source), cutoff=1)
            if max(grayscale.size) < 2100:
                factor = min(2.0, 2600 / max(grayscale.size))
                grayscale = grayscale.resize(
                    (round(grayscale.width * factor), round(grayscale.height * factor)),
                    Image.Resampling.LANCZOS,
                )
            # White/grey thermal paper benefits from improved local edge contrast.
            prepared = ImageEnhance.Contrast(grayscale).enhance(1.3).filter(
                ImageFilter.UnsharpMask(radius=1.2, percent=165, threshold=2)
            )
            best, best_score = "", -1

            def scan(candidate, psm: int) -> None:
                nonlocal best, best_score
                found = pytesseract.image_to_string(
                    candidate, config=f"--oem 3 --psm {psm}"
                ).strip()
                if found:
                    quality = _quality(found)
                    if quality > best_score or (quality == best_score and len(found) > len(best)):
                        best, best_score = found, quality

            scan(prepared, 6)
            scan(prepared, 11)
            if best_score < 5:
                scan(prepared.rotate(90, expand=True), 6)
                scan(prepared.rotate(270, expand=True), 6)
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrError(
            "Local OCR is unavailable because Tesseract is not installed or not on PATH."
        ) from exc
    except OcrError:
        raise
    except (UnidentifiedImageError, OSError) as exc:
        raise OcrError("Ledgergut could not read that image file.") from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise OcrError(
            "Ledgergut could not scan that receipt image. You can still enter it manually."
        ) from exc

    if best_score < 5:
        raise OcrError(
            "The photo didn't contain enough readable receipt information. "
            "Try a closer, sharper photo in even light, or review it manually."
        )
    return best
