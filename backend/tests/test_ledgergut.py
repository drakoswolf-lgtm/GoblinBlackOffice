"""
Tests for Ledgergut's extraction service.
"""

import os
import tempfile

from app.services.ledgergut import extract


class TestExtractTxt:
    def _write(self, content: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_extracts_vendor(self):
        path = self._write(
            "Acme Corp\n123 Main St\n03/15/2024\n\nTotal: $42.50\n"
        )
        result = extract(path)
        assert result.vendor == "Acme Corp"
        os.unlink(path)

    def test_extracts_date(self):
        path = self._write(
            "Big Store\nDate: 2024-01-20\nTotal $10.00\n"
        )
        result = extract(path)
        assert result.date == "2024-01-20"
        os.unlink(path)

    def test_extracts_total(self):
        path = self._write(
            "Coffee Shop\n2024-05-10\nCoffee     $4.50\nTotal Due $4.50\n"
        )
        result = extract(path)
        assert result.total == 4.50
        os.unlink(path)

    def test_fallback_largest_amount(self):
        path = self._write(
            "Some Store\n2024-02-14\n$5.00\n$12.99\n$1.00\n"
        )
        result = extract(path)
        assert result.total == 12.99
        assert any("largest" in w for w in result.warnings)
        os.unlink(path)

    def test_warns_on_missing_vendor(self):
        path = self._write(
            "12345\n03/10/2024\nTotal $7.00\n"
        )
        result = extract(path)
        assert any("vendor" in w.lower() for w in result.warnings)
        os.unlink(path)

    def test_warns_on_missing_date(self):
        path = self._write(
            "Good Shop\nSome items $5.00\nTotal $5.00\n"
        )
        result = extract(path)
        assert any("date" in w.lower() for w in result.warnings)
        os.unlink(path)

    def test_confidence_range(self):
        path = self._write("A\n")
        result = extract(path)
        assert 0.0 <= result.confidence <= 1.0
        os.unlink(path)


class TestExtractImageAndUnknown:
    def _stub(self, suffix: str) -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    def test_image_low_confidence(self):
        path = self._stub(".jpg")
        result = extract(path)
        assert result.confidence < 0.5
        assert result.warnings
        os.unlink(path)

    def test_unknown_extension_zero_confidence(self):
        path = self._stub(".xyz")
        result = extract(path)
        assert result.confidence == 0.0
        os.unlink(path)
