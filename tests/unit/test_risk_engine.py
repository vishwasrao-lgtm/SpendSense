"""Unit tests for RiskEngine."""

from datetime import datetime

import pytest

from src.risk_engine import RiskEngine
from tests.helpers import make_transaction


class TestEvaluateTransaction:
    """Tests for transaction evaluation."""

    def test_clean_transaction_not_flagged(self):
        engine = RiskEngine()
        txn = make_transaction(amount=10, monthly_budget_remaining=1000)
        assessment = engine.evaluate_transaction(txn)
        assert not assessment.is_flagged
        assert len(assessment.risk_flags) == 0

    def test_risky_transaction_flagged(self):
        engine = RiskEngine()
        txn = make_transaction(
            amount=600,
            monthly_budget_remaining=800,
            recipient_status="new",
        )
        assessment = engine.evaluate_transaction(txn)
        assert assessment.is_flagged
        assert len(assessment.risk_flags) >= 1

    def test_both_detectors_invoked(self):
        engine = RiskEngine()
        txn = make_transaction(
            amount=600,
            monthly_budget_remaining=800,
            recipient_status="new",
            timestamp=datetime(2026, 2, 28, 23, 0, 0),
        )
        assessment = engine.evaluate_transaction(txn)
        detector_types = {f.detector_type for f in assessment.risk_flags}
        assert "behavioral" in detector_types
        assert "contextual" in detector_types


class TestRecordDecision:
    """Tests for decision recording."""

    def test_record_cancelled(self):
        engine = RiskEngine()
        txn = make_transaction(amount=100)
        assessment = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        engine.record_decision(txn, assessment, "cancelled")
        assert len(engine.intercept_log) == 1
        assert engine.intercept_log[0].user_decision == "cancelled"
        assert engine.money_saved == 100.0

    def test_record_proceeded(self):
        engine = RiskEngine()
        txn = make_transaction(amount=100)
        assessment = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        engine.record_decision(txn, assessment, "proceeded")
        assert engine.intercept_log[0].user_decision == "proceeded"
        assert engine.money_saved == 0.0

    def test_money_saved_accumulates(self):
        engine = RiskEngine()
        for i in range(3):
            txn = make_transaction(txn_id=f"T{i}", amount=50)
            assessment = engine.evaluate_transaction(txn)
            engine.add_transaction(txn)
            engine.record_decision(txn, assessment, "cancelled")
        assert engine.money_saved == 150.0


class TestMetrics:
    """Tests for metrics computation."""

    def test_override_rate(self):
        engine = RiskEngine()
        # 2 flagged, 1 proceeded → override rate = 50%
        txn1 = make_transaction(txn_id="T1", amount=600, monthly_budget_remaining=800)
        a1 = engine.evaluate_transaction(txn1)
        engine.add_transaction(txn1)
        engine.record_decision(txn1, a1, "proceeded")

        txn2 = make_transaction(txn_id="T2", amount=600, monthly_budget_remaining=800)
        a2 = engine.evaluate_transaction(txn2)
        engine.add_transaction(txn2)
        engine.record_decision(txn2, a2, "cancelled")

        metrics = engine.get_metrics()
        assert metrics.override_rate == 50.0

    def test_impulsivity_score_range(self):
        engine = RiskEngine()
        txn = make_transaction(amount=10, monthly_budget_remaining=1000)
        engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        metrics = engine.get_metrics()
        assert 0 <= metrics.impulsivity_score <= 100


class TestInterceptLogFiltering:
    """Tests for intercept log filtering."""

    def test_filter_cancelled(self):
        engine = RiskEngine()
        txn1 = make_transaction(txn_id="T1", amount=100)
        a1 = engine.evaluate_transaction(txn1)
        engine.add_transaction(txn1)
        engine.record_decision(txn1, a1, "cancelled")

        txn2 = make_transaction(txn_id="T2", amount=200)
        a2 = engine.evaluate_transaction(txn2)
        engine.add_transaction(txn2)
        engine.record_decision(txn2, a2, "proceeded")

        cancelled = engine.get_intercept_log("cancelled")
        assert len(cancelled) == 1
        assert cancelled[0].user_decision == "cancelled"

    def test_filter_proceeded(self):
        engine = RiskEngine()
        txn = make_transaction(amount=100)
        a = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        engine.record_decision(txn, a, "proceeded")

        proceeded = engine.get_intercept_log("proceeded")
        assert len(proceeded) == 1
