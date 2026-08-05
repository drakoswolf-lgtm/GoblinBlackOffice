"""Convert raw OCR text into conservative Ledgergut receipt suggestions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ReceiptSuggestions:
    vendor_name: str | None
    receipt_date: date | None
    subtotal: Decimal | None
    tax_amount: Decimal | None
    total_amount: Decimal | None
    receipt_number: str | None
    raw_text: str
    confidence_notes: tuple[str, ...]


@dataclass(frozen=True)
class _AmountCandidate:
    amount: Decimal
    line_index: int
    label: str


_MONEY_RE = re.compile(r"(?<!\d)(?:CAD\s*)?\$?\s*([0-9]+(?:[.,][0-9]{2}))(?!\d)")
_NUMERIC_DATE_RE = re.compile(r"\b(\d{1,4})[/-](\d{1,2})[/-](\d{2,4})\b")
_MONTH_NAME_RE = re.compile(
    r"\b("
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
    r")\s+(\d{1,2})(?:,)?\s+(\d{4})\b"
    r"|\b(\d{1,2})\s+("
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*"
    r")\s+(\d{4})\b",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}")
_CARDISH_RE = re.compile(r"(?:\d[ -]?){13,19}")
_VENDOR_STOPWORDS = (
    "receipt",
    "invoice",
    "subtotal",
    "total",
    "tax",
    "amount",
    "gst",
    "pst",
    "hst",
    "change",
    "cash",
    "debit",
    "visa",
    "mastercard",
    "amex",
    "thank",
    "welcome",
    "transaction",
    "approval",
    "auth",
    "phone",
    "tel",
)
_MONTH_LOOKUP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}


def parse_receipt_text(raw_text: str) -> ReceiptSuggestions:
    """Parse OCR text into cautious receipt suggestions."""
    lines = _normalized_lines(raw_text)
    notes: list[str] = []

    vendor_name = _extract_vendor_name(lines)
    receipt_date, date_note = _extract_receipt_date(raw_text)
    if date_note:
        notes.append(date_note)

    subtotal = _extract_last_amount(
        lines,
        include=("subtotal", "sub total"),
        exclude=("tax", "gst", "pst", "hst"),
    )
    tax_amount, tax_note = _extract_tax_amount(lines)
    if tax_note:
        notes.append(tax_note)
    total_amount, total_note = _extract_total_amount(lines)
    if total_note:
        notes.append(total_note)
    receipt_number = _extract_receipt_number(lines)

    return ReceiptSuggestions(
        vendor_name=vendor_name,
        receipt_date=receipt_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        receipt_number=receipt_number,
        raw_text=raw_text,
        confidence_notes=tuple(notes),
    )


def _normalized_lines(raw_text: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", line).strip()
        for line in raw_text.splitlines()
        if line.strip()
    ]


def _extract_vendor_name(lines: list[str]) -> str | None:
    for line in lines[:6]:
        lowered = line.lower()
        if not re.search(r"[a-z]", lowered):
            continue
        if _PHONE_RE.search(line):
            continue
        if any(token in lowered for token in _VENDOR_STOPWORDS):
            continue
        if re.search(r"\b(?:street|st\.?|avenue|ave\.?|road|rd\.?|drive|dr\.?)\b", lowered):
            continue
        if len(re.findall(r"[a-z]", lowered)) < 3:
            continue
        return line
    return None


def _extract_receipt_date(raw_text: str) -> tuple[date | None, str | None]:
    for match in _MONTH_NAME_RE.finditer(raw_text):
        if match.group(1):
            month = _lookup_month(match.group(1))
            day = int(match.group(2))
            year = int(match.group(3))
        else:
            day = int(match.group(4))
            month = _lookup_month(match.group(5))
            year = int(match.group(6))
        try:
            return date(year, month, day), None
        except ValueError:
            continue

    for match in _NUMERIC_DATE_RE.finditer(raw_text):
        first = int(match.group(1))
        second = int(match.group(2))
        third = int(match.group(3))

        if first > 31:
            year = first
            month = second
            day = third
        elif third < 100:
            year = 2000 + third
            if first > 12 and second <= 12:
                day = first
                month = second
            elif second > 12 and first <= 12:
                month = first
                day = second
            else:
                return None, "OCR found an ambiguous receipt date, so the date suggestion was left blank."
        else:
            year = third
            if first > 12 and second <= 12:
                day = first
                month = second
            elif second > 12 and first <= 12:
                month = first
                day = second
            else:
                return None, "OCR found an ambiguous receipt date, so the date suggestion was left blank."
        try:
            return date(year, month, day), None
        except ValueError:
            continue

    return None, None


def _extract_tax_amount(lines: list[str]) -> tuple[Decimal | None, str | None]:
    labelled_candidates: dict[str, Decimal] = {}
    for label in ("gst", "pst", "hst"):
        amount = _extract_last_amount(lines, include=(label,), exclude=("total", "subtotal"))
        if amount is not None:
            labelled_candidates[label] = amount

    if labelled_candidates:
        return sum(labelled_candidates.values(), Decimal("0.00")), None

    generic_tax = _extract_last_amount(
        lines,
        include=("tax",),
        exclude=("subtotal", "total", "change", "cash", "auth", "approval"),
    )
    return generic_tax, None


def _extract_total_amount(lines: list[str]) -> tuple[Decimal | None, str | None]:
    candidates = _extract_amount_candidates(
        lines,
        include=("total", "amount due", "amount", "balance due"),
        exclude=(
            "subtotal",
            "sub total",
            "tax",
            "gst",
            "pst",
            "hst",
            "change",
            "cash",
            "tender",
            "tip",
            "debit",
            "visa",
            "mastercard",
            "amex",
            "approval",
            "auth",
            "phone",
            "tel",
        ),
    )
    if not candidates:
        return None, None

    bottom_candidate = candidates[-1]
    nearby_conflicts = {
        candidate.amount
        for candidate in candidates[:-1]
        if candidate.amount != bottom_candidate.amount
        and bottom_candidate.line_index - candidate.line_index <= 2
    }
    if nearby_conflicts:
        return None, "OCR found conflicting total amounts near the bottom, so the total suggestion was left blank."

    return bottom_candidate.amount, None


def _extract_receipt_number(lines: list[str]) -> str | None:
    patterns = (
        re.compile(
            r"\b(?:receipt|invoice|txn|transaction|order|ref)(?:\s*(?:no\.?|number|#|id))?\s*[:#-]?\s*([A-Z0-9-]{4,})\b",
            re.IGNORECASE,
        ),
    )
    for line in lines:
        lowered = line.lower()
        if "card" in lowered or "visa" in lowered or "mastercard" in lowered:
            continue
        for pattern in patterns:
            match = pattern.search(line)
            if not match:
                continue
            candidate = match.group(1).strip()
            if _CARDISH_RE.fullmatch(candidate):
                continue
            return candidate
    return None


def _extract_last_amount(
    lines: list[str],
    *,
    include: tuple[str, ...],
    exclude: tuple[str, ...] = (),
) -> Decimal | None:
    candidates = _extract_amount_candidates(lines, include=include, exclude=exclude)
    return candidates[-1].amount if candidates else None


def _extract_amount_candidates(
    lines: list[str],
    *,
    include: tuple[str, ...],
    exclude: tuple[str, ...] = (),
) -> list[_AmountCandidate]:
    candidates: list[_AmountCandidate] = []
    for line_index, line in enumerate(lines):
        lowered = line.lower()
        if not any(token in lowered for token in include):
            continue
        if any(token in lowered for token in exclude):
            continue
        if _PHONE_RE.search(line):
            continue
        if _CARDISH_RE.search(line):
            continue

        matches = _MONEY_RE.findall(line)
        if not matches:
            continue
        amount = _to_decimal(matches[-1])
        if amount is None:
            continue
        candidates.append(_AmountCandidate(amount=amount, line_index=line_index, label=line))
    return candidates


def _to_decimal(raw_amount: str) -> Decimal | None:
    cleaned = raw_amount.replace(",", "")
    try:
        return Decimal(cleaned)
    except Exception:  # pragma: no cover - defensive fallback
        return None


def _lookup_month(raw_month: str) -> int:
    key = raw_month.lower().rstrip(".")
    if key.startswith("sept"):
        return _MONTH_LOOKUP["sept"]
    return _MONTH_LOOKUP[key[:3]]
