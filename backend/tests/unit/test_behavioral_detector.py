"""Unit tests for BehavioralDetector."""

from datetime import datetime

import pytest

from src.detectors import BehavioralDetector
from tests.helpers import make_transaction


class TestBudgetDrain:
    """Tests for budget drain detection."""

    def test_flags_over_50_percent(self):
        txn = make_transaction(amount=100, monthly_budget_remaining=150)
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "budget_drain" for f in flags)

    def test_no_flag_under_50_percent(self):
        txn = make_transaction(amount=100, monthly_budget_remaining=500)
        flags = BehavioralDetector().detect(txn)
        assert not any(f.rule_name == "budget_drain" for f in flags)

    def test_boundary_exactly_50_percent(self):
        # amount == 50% of budget → NOT flagged (must exceed)
        txn = make_transaction(amount=50, monthly_budget_remaining=100)
        flags = BehavioralDetector().detect(txn)
        assert not any(f.rule_name == "budget_drain" for f in flags)

    def test_zero_budget_remaining(self):
        txn = make_transaction(amount=10, monthly_budget_remaining=0)
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "budget_drain" for f in flags)

    def test_negative_budget_remaining(self):
        txn = make_transaction(amount=10, monthly_budget_remaining=-50)
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "budget_drain" for f in flags)


class TestLateNightRegret:
    """Tests for late-night pattern detection."""

    def test_flags_at_11pm(self):
        txn = make_transaction(timestamp=datetime(2026, 2, 28, 23, 0, 0))
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "late_night_regret" for f in flags)

    def test_flags_at_2am(self):
        txn = make_transaction(timestamp=datetime(2026, 2, 28, 2, 0, 0))
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "late_night_regret" for f in flags)

    def test_boundary_10pm(self):
        txn = make_transaction(timestamp=datetime(2026, 2, 28, 22, 0, 0))
        flags = BehavioralDetector().detect(txn)
        assert any(f.rule_name == "late_night_regret" for f in flags)

    def test_boundary_4am_not_flagged(self):
        txn = make_transaction(timestamp=datetime(2026, 2, 28, 4, 0, 0))
        flags = BehavioralDetector().detect(txn)
        assert not any(f.rule_name == "late_night_regret" for f in flags)

    def test_daytime_not_flagged(self):
        txn = make_transaction(timestamp=datetime(2026, 2, 28, 14, 0, 0))
        flags = BehavioralDetector().detect(txn)
        assert not any(f.rule_name == "late_night_regret" for f in flags)
