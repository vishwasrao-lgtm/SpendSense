"""Property-based tests for decision recording (Properties 16–18)."""

from datetime import datetime

from hypothesis import given, settings, strategies as st

from src.models import Transaction
from src.risk_engine import RiskEngine


def _make_txn(txn_id: str, amount: float) -> Transaction:
    return Transaction(
        txn_id=txn_id, user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
        amount=amount, category="shopping", recipient_status="new",
        monthly_budget_remaining=amount * 0.9,  # will trigger budget drain
        device_id="D", location="NY", channel="web",
    )


# Feature: transaction-intervention-system, Property 16: Cancelled Transaction Recording
@given(amount=st.floats(min_value=0.01, max_value=10000))
@settings(max_examples=100)
def test_cancelled_transaction_recorded(amount):
    engine = RiskEngine()
    txn = _make_txn("T", amount)
    assessment = engine.evaluate_transaction(txn)
    engine.add_transaction(txn)
    engine.record_decision(txn, assessment, "cancelled")

    log = engine.get_intercept_log()
    assert len(log) == 1
    assert log[0].user_decision == "cancelled"
    assert log[0].decision_timestamp is not None
    assert len(log[0].risk_explanations) > 0


# Feature: transaction-intervention-system, Property 17: Proceeded Transaction Recording
@given(amount=st.floats(min_value=0.01, max_value=10000))
@settings(max_examples=100)
def test_proceeded_transaction_recorded(amount):
    engine = RiskEngine()
    txn = _make_txn("T", amount)
    assessment = engine.evaluate_transaction(txn)
    engine.add_transaction(txn)
    engine.record_decision(txn, assessment, "proceeded")

    log = engine.get_intercept_log()
    assert len(log) == 1
    assert log[0].user_decision == "proceeded"
    assert log[0].decision_timestamp is not None


# Feature: transaction-intervention-system, Property 18: Money Saved Counter Increment
@given(amount=st.floats(min_value=0.01, max_value=10000))
@settings(max_examples=100)
def test_money_saved_increments_on_cancel(amount):
    engine = RiskEngine()
    txn = _make_txn("T", amount)
    assessment = engine.evaluate_transaction(txn)
    engine.add_transaction(txn)

    saved_before = engine.get_money_saved()
    engine.record_decision(txn, assessment, "cancelled")
    saved_after = engine.get_money_saved()

    assert abs((saved_after - saved_before) - amount) < 0.01
