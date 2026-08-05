from __future__ import annotations

import io
from datetime import date
from decimal import Decimal

import pytest
import pytesseract
from PIL import Image

from app.ledgergut.ocr import OcrError, extract_text_from_image
from app.ledgergut.receipt_parser import parse_receipt_text


def _png_bytes() -> bytes:
    image = Image.new("RGB", (16, 16), "white")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_extract_text_from_image_returns_mocked_ocr_text(monkeypatch) -> None:
    monkeypatch.setattr(
        pytesseract,
        "image_to_string",
        lambda image: "HOME HARDWARE\nTOTAL 28.00\n",
    )

    assert extract_text_from_image(_png_bytes()) == "HOME HARDWARE\nTOTAL 28.00"


def test_extract_text_from_image_surfaces_user_facing_failure(monkeypatch) -> None:
    def _raise_not_found(_image):
        raise pytesseract.TesseractNotFoundError()

    monkeypatch.setattr(pytesseract, "image_to_string", _raise_not_found)

    with pytest.raises(OcrError, match="not installed or not on PATH"):
        extract_text_from_image(_png_bytes())


def test_parse_receipt_text_extracts_vendor_amounts_and_receipt_number() -> None:
    suggestions = parse_receipt_text(
        "\n".join(
            [
                "HOME HARDWARE",
                "123 Main Street",
                "GST 1.25",
                "PST 1.75",
                "SUBTOTAL 25.00",
                "TOTAL 28.00",
                "Receipt #: RCT-00421",
            ]
        )
    )

    assert suggestions.vendor_name == "HOME HARDWARE"
    assert suggestions.subtotal == Decimal("25.00")
    assert suggestions.tax_amount == Decimal("3.00")
    assert suggestions.total_amount == Decimal("28.00")
    assert suggestions.receipt_number == "RCT-00421"


def test_parse_receipt_text_supports_common_date_formats() -> None:
    assert parse_receipt_text("Date: 2026-07-01").receipt_date == date(2026, 7, 1)
    assert parse_receipt_text("Date: 13/07/2026").receipt_date == date(2026, 7, 13)
    assert parse_receipt_text("Date: Jul 1 2026").receipt_date == date(2026, 7, 1)


def test_parse_receipt_text_rejects_ambiguous_totals() -> None:
    suggestions = parse_receipt_text(
        "\n".join(
            [
                "Shop Mart",
                "SUBTOTAL 10.00",
                "TOTAL 11.30",
                "AMOUNT DUE 12.50",
            ]
        )
    )

    assert suggestions.total_amount is None
    assert any("conflicting total amounts" in note for note in suggestions.confidence_notes)


def test_parse_receipt_text_ignores_phone_numbers_and_card_numbers() -> None:
    suggestions = parse_receipt_text(
        "\n".join(
            [
                "Coffee Spot",
                "Phone 604-555-0100",
                "Visa 4111 1111 1111 1111",
                "SUBTOTAL 12.00",
                "TAX 0.60",
                "TOTAL 12.60",
            ]
        )
    )

    assert suggestions.vendor_name == "Coffee Spot"
    assert suggestions.total_amount == Decimal("12.60")
    assert suggestions.receipt_number is None
