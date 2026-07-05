"""Unit tests for KPI helper utilities."""

import pytest
from decimal import Decimal


class TestLineTotal:
    """Tests for line_total() function."""

    def test_basic_calculation(self):
        """Normal case: quantity * unit price."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = 5
            prix_unitaire_ht = Decimal("12.50")

        result = line_total(FakeLine)
        assert result == Decimal("62.50")

    def test_zero_quantity(self):
        """Zero quantity should yield zero total."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = 0
            prix_unitaire_ht = Decimal("100.00")

        result = line_total(FakeLine)
        assert result == Decimal("0")

    def test_zero_price(self):
        """Zero price should yield zero total."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = 10
            prix_unitaire_ht = Decimal("0")

        result = line_total(FakeLine)
        assert result == Decimal("0")

    def test_none_values(self):
        """None quantity or price should be treated as zero."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = None
            prix_unitaire_ht = None

        result = line_total(FakeLine)
        assert result == Decimal("0")

    def test_missing_attributes(self):
        """Missing attributes should be treated as zero."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            pass

        result = line_total(FakeLine)
        assert result == Decimal("0")

    def test_float_values(self):
        """Float values should be converted to Decimal."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = 3
            prix_unitaire_ht = 9.99

        result = line_total(FakeLine)
        assert isinstance(result, Decimal)
        assert result == Decimal("29.97")


class TestDecimalConversion:
    """Verify Decimal arithmetic works as expected."""

    def test_decimal_precision(self):
        """Decimal arithmetic preserves precision unlike float."""
        a = Decimal("0.1") + Decimal("0.2")
        assert a == Decimal("0.3")
        # Float would give 0.30000000000000004
        b = 0.1 + 0.2
        assert b != 0.3


class TestNumericBoundaries:
    """Edge cases for numeric inputs."""

    def test_large_values(self):
        """Large values should not overflow."""
        from app.utils.kpi_helpers import line_total

        class FakeLine:
            quantite_commandee = 1_000_000
            prix_unitaire_ht = Decimal("999999.9999")

        result = line_total(FakeLine)
        assert result > Decimal("0")
        assert result == Decimal("999999999900.0000")
