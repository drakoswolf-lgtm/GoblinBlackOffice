import pytest
from decimal import Decimal
from app.core.money import to_decimal, round_currency, within_rounding_tolerance


def test_to_decimal_from_int():
    assert to_decimal(5) == Decimal("5")


def test_to_decimal_from_float():
    result = to_decimal(1.1)
    assert isinstance(result, Decimal)
    assert result == Decimal("1.1")


def test_to_decimal_from_string():
    assert to_decimal("3.14") == Decimal("3.14")


def test_to_decimal_from_decimal():
    d = Decimal("9.99")
    assert to_decimal(d) is d


def test_round_currency_rounds_half_up():
    assert round_currency("2.345") == Decimal("2.35")
    assert round_currency("2.344") == Decimal("2.34")


def test_round_currency_two_decimal_places():
    result = round_currency(10)
    assert result == Decimal("10.00")
    assert str(result) == "10.00"


def test_round_currency_negative():
    assert round_currency("-1.005") == Decimal("-1.01")
    assert round_currency("-1.004") == Decimal("-1.00")


def test_round_currency_already_rounded():
    assert round_currency(Decimal("5.50")) == Decimal("5.50")


def test_within_rounding_tolerance_equal():
    assert within_rounding_tolerance(10.00, 10.00) is True


def test_within_rounding_tolerance_within():
    assert within_rounding_tolerance(10.00, 10.04) is True
    assert within_rounding_tolerance(10.00, 9.96) is True


def test_within_rounding_tolerance_at_boundary():
    assert within_rounding_tolerance(10.00, 10.05) is True
    assert within_rounding_tolerance(10.00, 9.95) is True


def test_within_rounding_tolerance_outside():
    assert within_rounding_tolerance(10.00, 10.06) is False
    assert within_rounding_tolerance(10.00, 9.94) is False


def test_within_rounding_tolerance_custom_tolerance():
    assert within_rounding_tolerance(10.00, 10.10, tolerance=0.10) is True
    assert within_rounding_tolerance(10.00, 10.11, tolerance=0.10) is False


def test_within_rounding_tolerance_decimal_inputs():
    a = Decimal("100.00")
    b = Decimal("100.03")
    assert within_rounding_tolerance(a, b) is True


def test_within_rounding_tolerance_string_inputs():
    assert within_rounding_tolerance("50.00", "50.04") is True
    assert within_rounding_tolerance("50.00", "50.06") is False
