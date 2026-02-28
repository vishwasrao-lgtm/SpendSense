"""Unit tests for Dashboard calculations."""

import pytest

from src.dashboard import Dashboard
from tests.helpers import make_transaction


class TestImpulsivityScore:
    """Tests for impulsivity score."""

    def test_score_in_range(self):
        score = Dashboard.calculate_impulsivity_score(50.0, 5, 20)
        assert 0 <= score <= 100

    def test_zero_inputs(self):
        score = Dashboard.calculate_impulsivity_score(0.0, 0, 0)
        assert score == 0.0

    def test_max_inputs(self):
        score = Dashboard.calculate_impulsivity_score(100.0, 100, 100)
        assert score == 100.0

    def test_partial_inputs(self):
        score = Dashboard.calculate_impulsivity_score(50.0, 0, 10)
        # 0.6 * 50 + 0.4 * 0 = 30
        assert abs(score - 30.0) < 0.1


class TestTransactionStyle:
    """Tests for color coding."""

    def test_clean_is_green(self):
        txn = make_transaction()
        txn.is_flagged = False
        color, icon = Dashboard._get_transaction_style(txn)
        assert color == "green"

    def test_cancelled_is_red(self):
        txn = make_transaction()
        txn.is_flagged = True
        txn.user_decision = "cancelled"
        color, icon = Dashboard._get_transaction_style(txn)
        assert color == "red"

    def test_proceeded_is_orange(self):
        txn = make_transaction()
        txn.is_flagged = True
        txn.user_decision = "proceeded"
        color, icon = Dashboard._get_transaction_style(txn)
        assert color == "orange"
