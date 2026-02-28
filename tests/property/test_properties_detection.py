"""Property-based tests for risk detection (Properties 4–10)."""

from datetime import datetime, timedelta

from hypothesis import given, settings, strategies as st

from src.detectors import BehavioralDetector, ContextualDetector
from src.models import RiskFlag, Transaction
from src.risk_engine import RiskEngine


def _transaction_strategy(**overrides):
    """Build a Hypothesis strategy for Transaction objects."""
    defaults = {
        "txn_id": st.uuids().map(str),
        "user_id": st.just("USR_TEST"),
        "timestamp": st.datetimes(
            min_value=datetime(2020, 1, 1),
            max_value=datetime(2027, 12, 31),
        ),
        "amount": st.floats(min_value=0.01, max_value=10000),
        "category": st.sampled_from(["groceries", "dining", "entertainment", "shopping", "bills"]),
        "recipient_status": st.sampled_from(["new", "existing"]),
        "monthly_budget_remaining": st.floats(min_value=0.01, max_value=50000),
        "device_id": st.text(min_size=1, max_size=20),
        "location": st.text(min_size=1, max_size=50),
        "channel": st.sampled_from(["mobile_app", "web", "pos"]),
    }
    defaults.update(overrides)
    return st.builds(Transaction, **defaults)


# Feature: transaction-intervention-system, Property 4: Budget Drain Detection
@given(amount=st.floats(min_value=0.01, max_value=10000))
@settings(max_examples=100)
def test_budget_drain_detection(amount):
    budget = amount * 0.9  # amount > 50% of budget since 0.9 < 2*amount
    txn = Transaction(
        txn_id="T", user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
        amount=amount, category="shopping", recipient_status="existing",
        monthly_budget_remaining=budget, device_id="D", location="NY", channel="web",
    )
    detector = BehavioralDetector()
    flags = detector.detect(txn)
    assert any(f.rule_name == "budget_drain" for f in flags)


# Feature: transaction-intervention-system, Property 5: Late-Night Pattern Detection
@given(hour=st.sampled_from(list(range(22, 24)) + list(range(0, 4))))
@settings(max_examples=100)
def test_late_night_detection(hour):
    txn = Transaction(
        txn_id="T", user_id="U", timestamp=datetime(2026, 1, 1, hour, 30),
        amount=10, category="shopping", recipient_status="existing",
        monthly_budget_remaining=1000, device_id="D", location="NY", channel="web",
    )
    detector = BehavioralDetector()
    flags = detector.detect(txn)
    assert any(f.rule_name == "late_night_regret" for f in flags)


# Feature: transaction-intervention-system, Property 6: New Recipient Detection
@given(txn=_transaction_strategy(recipient_status=st.just("new")))
@settings(max_examples=100)
def test_new_recipient_detection(txn):
    detector = ContextualDetector()
    flags = detector.detect(txn, [])
    assert any(f.rule_name == "new_recipient" for f in flags)


# Feature: transaction-intervention-system, Property 7: Frequency Burst Detection
@given(base_time=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2027, 1, 1)))
@settings(max_examples=100)
def test_frequency_burst_detection(base_time):
    recent = [
        Transaction(
            txn_id=f"T{i}", user_id="U", timestamp=base_time - timedelta(minutes=i + 1),
            amount=10, category="shopping", recipient_status="existing",
            monthly_budget_remaining=1000, device_id="D", location="NY", channel="web",
        )
        for i in range(2)
    ]
    current = Transaction(
        txn_id="TC", user_id="U", timestamp=base_time,
        amount=10, category="shopping", recipient_status="existing",
        monthly_budget_remaining=1000, device_id="D", location="NY", channel="web",
    )
    detector = ContextualDetector()
    flags = detector.detect(current, recent)
    assert any(f.rule_name == "frequency_burst" for f in flags)


# Feature: transaction-intervention-system, Property 8: Device Anomaly Detection
@given(
    known_device=st.text(min_size=1, max_size=10),
    new_device=st.text(min_size=1, max_size=10),
)
@settings(max_examples=100)
def test_device_anomaly_detection(known_device, new_device):
    from hypothesis import assume
    assume(known_device != new_device)

    now = datetime(2026, 1, 1, 12, 0)
    recent = [
        Transaction(
            txn_id="T1", user_id="U", timestamp=now - timedelta(hours=1),
            amount=10, category="shopping", recipient_status="existing",
            monthly_budget_remaining=1000, device_id=known_device, location="NY", channel="web",
        )
    ]
    current = Transaction(
        txn_id="TC", user_id="U", timestamp=now,
        amount=10, category="shopping", recipient_status="existing",
        monthly_budget_remaining=1000, device_id=new_device, location="NY", channel="web",
    )
    detector = ContextualDetector()
    flags = detector.detect(current, recent)
    assert any(f.rule_name == "device_anomaly" for f in flags)


# Feature: transaction-intervention-system, Property 9: Location Anomaly Detection
@given(
    known_loc=st.text(min_size=1, max_size=20),
    new_loc=st.text(min_size=1, max_size=20),
)
@settings(max_examples=100)
def test_location_anomaly_detection(known_loc, new_loc):
    from hypothesis import assume
    assume(known_loc != new_loc)

    now = datetime(2026, 1, 1, 12, 0)
    recent = [
        Transaction(
            txn_id="T1", user_id="U", timestamp=now - timedelta(hours=1),
            amount=10, category="shopping", recipient_status="existing",
            monthly_budget_remaining=1000, device_id="D", location=known_loc, channel="web",
        )
    ]
    current = Transaction(
        txn_id="TC", user_id="U", timestamp=now,
        amount=10, category="shopping", recipient_status="existing",
        monthly_budget_remaining=1000, device_id="D", location=new_loc, channel="web",
    )
    detector = ContextualDetector()
    flags = detector.detect(current, recent)
    assert any(f.rule_name == "location_anomaly" for f in flags)


# Feature: transaction-intervention-system, Property 10: Risk Flag Recording
@given(txn=_transaction_strategy(
    recipient_status=st.just("new"),
    amount=st.just(600.0),
    monthly_budget_remaining=st.just(800.0),
))
@settings(max_examples=100)
def test_risk_flags_recorded_in_intercept_log(txn):
    engine = RiskEngine()
    assessment = engine.evaluate_transaction(txn)
    engine.add_transaction(txn)
    if assessment.is_flagged:
        engine.record_decision(txn, assessment, "cancelled")
        log = engine.get_intercept_log()
        assert len(log) == 1
        assert len(log[0].risk_flags) == len(assessment.risk_flags)
        for flag in log[0].risk_flags:
            assert flag.rule_name
            assert flag.explanation
            assert flag.detector_type in ("behavioral", "contextual")
