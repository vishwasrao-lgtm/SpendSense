"""Property-based tests for UI (Properties 11–15)."""

from datetime import datetime

from hypothesis import given, settings, strategies as st

from src.models import RiskAssessment, RiskFlag, Transaction
from src.ui import InterventionUI


def _make_flagged_assessment(amount: float, budget: float):
    """Create a RiskAssessment with at least one flag for testing."""
    txn = Transaction(
        txn_id="T", user_id="U", timestamp=datetime(2026, 1, 1, 12, 0),
        amount=amount, category="shopping", recipient_status="new",
        monthly_budget_remaining=budget, device_id="D", location="NY", channel="web",
    )
    flags = [
        RiskFlag(
            rule_name="budget_drain",
            explanation=f"Uses {amount/budget*100:.0f}% of budget" if budget > 0 else "Over budget",
            severity="high",
            detector_type="behavioral",
        )
    ]
    return RiskAssessment(transaction=txn, risk_flags=flags, is_flagged=True)


# Feature: transaction-intervention-system, Property 12: Compound Interest Calculation
@given(amount=st.floats(min_value=0.01, max_value=100000))
@settings(max_examples=100)
def test_compound_interest_formula(amount):
    result = InterventionUI.calculate_future_impact(amount)
    for years, label in [(1, "1 Year"), (5, "5 Years"), (10, "10 Years")]:
        expected = amount * (1.07 ** years)
        assert abs(result[label] - expected) < 0.01


# Feature: transaction-intervention-system, Property 13: Future Impact Projection Completeness
@given(amount=st.floats(min_value=0.01, max_value=100000))
@settings(max_examples=100)
def test_future_impact_has_three_periods(amount):
    result = InterventionUI.calculate_future_impact(amount)
    assert len(result) == 3
    assert "1 Year" in result
    assert "5 Years" in result
    assert "10 Years" in result
