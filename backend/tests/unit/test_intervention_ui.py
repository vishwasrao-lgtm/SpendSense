"""Unit tests for InterventionUI calculations."""

import pytest

from src.ui import InterventionUI


class TestFutureImpact:
    """Tests for compound interest projections."""

    def test_projection_keys(self):
        result = InterventionUI.calculate_future_impact(100)
        assert set(result.keys()) == {"1 Year", "5 Years", "10 Years"}

    def test_1_year_calculation(self):
        result = InterventionUI.calculate_future_impact(100)
        expected = 100 * (1.07 ** 1)
        assert abs(result["1 Year"] - expected) < 0.01

    def test_5_year_calculation(self):
        result = InterventionUI.calculate_future_impact(100)
        expected = 100 * (1.07 ** 5)
        assert abs(result["5 Years"] - expected) < 0.01

    def test_10_year_calculation(self):
        result = InterventionUI.calculate_future_impact(100)
        expected = 100 * (1.07 ** 10)
        assert abs(result["10 Years"] - expected) < 0.01

    def test_zero_amount(self):
        result = InterventionUI.calculate_future_impact(0)
        assert all(v == 0.0 for v in result.values())
