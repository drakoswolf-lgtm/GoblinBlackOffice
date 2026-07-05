from decimal import Decimal, ROUND_HALF_UP


def to_decimal(value) -> Decimal:
    """Convert a value to Decimal, suitable for currency calculations."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def round_currency(value) -> Decimal:
    """Round a value to two decimal places using ROUND_HALF_UP."""
    return to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def within_rounding_tolerance(a, b, tolerance: float = 0.05) -> bool:
    """Return True if the absolute difference between a and b is within tolerance."""
    diff = abs(round_currency(a) - round_currency(b))
    return diff <= to_decimal(tolerance)
