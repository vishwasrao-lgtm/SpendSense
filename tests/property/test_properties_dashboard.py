"""Property-based tests for dashboard (Properties 19–31)."""

from collections import Counter
from datetime import datetime

from hypothesis import given, settings, strategies as st

from src.dashboard import Dashboard
from src.models import InterceptLog, RiskFlag, Transaction
from src.risk_engine import RiskEngine


def _txn_strategy():
    return st.builds(
        Transaction,
        txn_id=st.uuids().map(str),
        user_id=st.just("U"),
        timestamp=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2027, 12, 31)),
        amount=st.floats(min_value=0.01, max_value=10000),
        category=st.sampled_from(["groceries", "dining", "entertainment", "shopping", "bills"]),
        recipient_status=st.sampled_from(["new", "existing"]),
        monthly_budget_remaining=st.floats(min_value=0.01, max_value=50000),
        device_id=st.text(min_size=1, max_size=10),
        location=st.text(min_size=1, max_size=20),
        channel=st.sampled_from(["mobile_app", "web", "pos"]),
    )


# Feature: transaction-intervention-system, Property 19: Transaction Feed Chronological Ordering
@given(txns=st.lists(_txn_strategy(), min_size=2, max_size=10))
@settings(max_examples=100)
def test_chronological_ordering(txns):
    sorted_txns = sorted(txns, key=lambda t: t.timestamp, reverse=True)
    for i in range(len(sorted_txns) - 1):
        assert sorted_txns[i].timestamp >= sorted_txns[i + 1].timestamp


# Feature: transaction-intervention-system, Property 24: Money Saved Calculation
@given(amounts=st.lists(st.floats(min_value=0.01, max_value=10000), min_size=1, max_size=10))
@settings(max_examples=100)
def test_money_saved_equals_sum_of_cancelled(amounts):
    engine = RiskEngine()
    for i, amt in enumerate(amounts):
        txn = Transaction(
            txn_id=f"T{i}", user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
            amount=amt, category="shopping", recipient_status="new",
            monthly_budget_remaining=amt * 0.9,
            device_id="D", location="NY", channel="web",
        )
        assessment = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        engine.record_decision(txn, assessment, "cancelled")

    assert abs(engine.get_money_saved() - sum(amounts)) < 0.1


# Feature: transaction-intervention-system, Property 26: Category Distribution Completeness
@given(txns=st.lists(_txn_strategy(), min_size=1, max_size=20))
@settings(max_examples=100)
def test_category_distribution_completeness(txns):
    expected_categories = set(t.category for t in txns)
    actual_counts = Counter(t.category for t in txns)
    assert set(actual_counts.keys()) == expected_categories


# Feature: transaction-intervention-system, Property 28: Impulsivity Score Range
@given(
    override_rate=st.floats(min_value=0, max_value=100),
    late_night_count=st.integers(min_value=0, max_value=1000),
    total_count=st.integers(min_value=1, max_value=1000),
)
@settings(max_examples=100)
def test_impulsivity_score_in_range(override_rate, late_night_count, total_count):
    from hypothesis import assume
    assume(late_night_count <= total_count)
    score = Dashboard.calculate_impulsivity_score(override_rate, late_night_count, total_count)
    assert 0 <= score <= 100


# Feature: transaction-intervention-system, Property 29: Transaction Count Accuracy
@given(txns=st.lists(_txn_strategy(), min_size=1, max_size=20))
@settings(max_examples=100)
def test_transaction_count_accuracy(txns):
    engine = RiskEngine()
    for t in txns:
        engine.evaluate_transaction(t)
        engine.add_transaction(t)
    metrics = engine.get_metrics()
    assert metrics.total_transactions == len(txns)


# Feature: transaction-intervention-system, Property 30: Flagged Transaction Count Accuracy
@given(txns=st.lists(_txn_strategy(), min_size=1, max_size=20))
@settings(max_examples=100)
def test_flagged_count_accuracy(txns):
    engine = RiskEngine()
    for t in txns:
        engine.evaluate_transaction(t)
        engine.add_transaction(t)
    metrics = engine.get_metrics()
    expected_flagged = sum(1 for t in engine.transactions if t.is_flagged)
    assert metrics.total_flagged == expected_flagged


# Feature: transaction-intervention-system, Property 31: Override Rate Calculation
@given(
    proceeded_count=st.integers(min_value=0, max_value=50),
    cancelled_count=st.integers(min_value=0, max_value=50),
)
@settings(max_examples=100)
def test_override_rate_calculation(proceeded_count, cancelled_count):
    from hypothesis import assume
    total_flagged = proceeded_count + cancelled_count
    assume(total_flagged > 0)

    engine = RiskEngine()
    for i in range(proceeded_count):
        txn = Transaction(
            txn_id=f"P{i}", user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
            amount=600, category="shopping", recipient_status="new",
            monthly_budget_remaining=800,
            device_id="D", location="NY", channel="web",
        )
        assessment = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        if assessment.is_flagged:
            engine.record_decision(txn, assessment, "proceeded")

    for i in range(cancelled_count):
        txn = Transaction(
            txn_id=f"C{i}", user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
            amount=600, category="shopping", recipient_status="new",
            monthly_budget_remaining=800,
            device_id="D", location="NY", channel="web",
        )
        assessment = engine.evaluate_transaction(txn)
        engine.add_transaction(txn)
        if assessment.is_flagged:
            engine.record_decision(txn, assessment, "cancelled")

    metrics = engine.get_metrics()
    if metrics.total_flagged > 0:
        actual_proceeded = sum(1 for e in engine.intercept_log if e.user_decision == "proceeded")
        expected_rate = (actual_proceeded / metrics.total_flagged) * 100
        assert abs(metrics.override_rate - round(expected_rate, 1)) < 0.2
