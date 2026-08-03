"""Local OCR helpers for Ledgergut receipt scanning."""

from __future__ import annotations

from io import BytesIO


class OcrError(Exception):
    """Raised when local OCR cannot produce usable receipt text."""


def extract_text_from_image(image_bytes: bytes) -> str:
    """Return OCR text from a receipt image using local Tesseract."""
    try:
        import pytesseract
        from PIL import Image, ImageOps, UnidentifiedImageError
    except ImportError as exc:
        raise OcrError(
            "Local OCR is unavailable because the OCR dependencies are not installed."
        ) from exc

    try:
        with Image.open(BytesIO(image_bytes)) as image:
            normalized = ImageOps.exif_transpose(image)
            raw_text = pytesseract.image_to_string(normalized)
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrError(
            "Local OCR is unavailable because Tesseract is not installed or not on PATH."
        ) from exc
    except UnidentifiedImageError as exc:
        raise OcrError("Ledgergut could not read that image file.") from exc
    except OSError as exc:
        raise OcrError("Ledgergut could not read that image file.") from exc
    except Exception as exc:  # pragma: no cover - defensive fallback
        raise OcrError(
            "Ledgergut could not scan that receipt image. You can still enter it manually."
        ) from exc

    text = raw_text.strip()
    if not text:
        raise OcrError(
            "Ledgergut could not detect readable text in that receipt image. "
            "You can still enter it manually."
        )
    return text
